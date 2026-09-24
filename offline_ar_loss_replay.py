#!/usr/bin/env python3
"""Offline AR-loss replay for the YuE2 AR-only pronunciation LoRA.

ai-toolkit's diffusion trainer has no audio validation hook (image-only), so the
180 `val` pairs are never scored during the pron run. This script closes that gap
without a trainer: for one checkpoint it loads the base YuE2 model, attaches the
saved AR-only adapter through the real `convert_lora_weights_before_load` hook,
and runs the exact per-item AR next-token loss path training used
(`YuE2AudioModel._prefix_segment` / `_item_prefix_and_abc` / `_ar_inputs` /
`_ar_losses`, yue2_model.py:506-704) over the val pairs.

Reported per item and in aggregate: `loss/ar_ce` and `loss/ar_kl` (KL(base||lora)
over the AR next-token distributions, base = adapter switched off).

Forward passes only: no backward, no optimizer, no trainer, no NAR flow forward.
The NAR forward is what training additionally runs for the flow loss; it does not
contribute to ar_ce/ar_kl and is skipped here on purpose.

Usage:
    python offline_ar_loss_replay.py --checkpoint final --limit 8
    python offline_ar_loss_replay.py --checkpoint 4575 --out results_4575.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "pron_lora_ar_only.yml"
DEFAULT_RUN_DIR = Path("/content/ai-toolkit/output/pron_lora_ar_only_r8")
DEFAULT_VAL_DIR = Path("/content/pron_dataset/val")
DEFAULT_AI_TOOLKIT_DIR = Path(os.environ.get("AI_TOOLKIT_DIR", "/content/ai-toolkit"))

# the four trainable pron artifacts; there is no _000006100 numbered file --
# the post-loop no-step save is the step-6100 artifact.
CHECKPOINT_FILES: Dict[str, str] = {
    "1525": "pron_lora_ar_only_r8_000001525.safetensors",
    "3050": "pron_lora_ar_only_r8_000003050.safetensors",
    "4575": "pron_lora_ar_only_r8_000004575.safetensors",
    "final": "pron_lora_ar_only_r8.safetensors",
}


class ReplayError(RuntimeError):
    pass


@dataclass
class ItemResult:
    index: int
    stem: str
    caption_tokens: int
    ar_target_tokens: int
    ar_ce: float
    ar_kl: Optional[float]
    tokenize_s: float
    loss_s: float

    @property
    def total_s(self) -> float:
        return self.tokenize_s + self.loss_s


def resolve_checkpoint(run_dir: Path, name: str) -> Path:
    """Map a checkpoint name (1525/3050/4575/final) to its file under ``run_dir``."""
    if name not in CHECKPOINT_FILES:
        raise ReplayError(
            f"unknown checkpoint {name!r}; expected one of {sorted(CHECKPOINT_FILES)}"
        )
    path = Path(run_dir) / CHECKPOINT_FILES[name]
    if not path.is_file():
        raise ReplayError(
            f"adapter not staged: {path} (pull the run's output/ prefix from GCS)"
        )
    return path


def list_val_pairs(val_dir: Path) -> List[Tuple[str, Path, Path]]:
    """Sorted (stem, mp3, txt) for every val pair that has both files."""
    val_dir = Path(val_dir)
    if not val_dir.is_dir():
        raise ReplayError(f"val dir not found: {val_dir}")
    out: List[Tuple[str, Path, Path]] = []
    for mp3 in sorted(val_dir.glob("*.mp3")):
        txt = mp3.with_suffix(".txt")
        if txt.is_file():
            out.append((mp3.stem, mp3, txt))
    if not out:
        raise ReplayError(f"no (mp3, txt) pairs found under {val_dir}")
    return out


def mean_losses(results: Sequence[ItemResult]) -> Tuple[float, Optional[float]]:
    """Mean ar_ce and mean ar_kl (None when no item produced a KL)."""
    if not results:
        raise ReplayError("no results to average")
    ce = sum(r.ar_ce for r in results) / len(results)
    kls = [r.ar_kl for r in results if r.ar_kl is not None]
    kl = sum(kls) / len(kls) if kls else None
    return ce, kl


def load_config_sections(config_path: Path) -> Tuple[dict, dict]:
    """(model, network) sections from a pron run config -- the same dicts the
    trainer turns into ModelConfig / NetworkConfig."""
    import yaml

    data = yaml.safe_load(Path(config_path).read_text())
    process = data["config"]["process"][0]
    return process["model"], process["network"]


def _import_ai_toolkit(ai_dir: Path):
    ai_dir = str(ai_dir)
    if ai_dir not in sys.path:
        sys.path.insert(0, ai_dir)


def build_model(model_cfg: dict, ai_dir: Path, device: str = "cpu"):
    _import_ai_toolkit(ai_dir)
    from extensions_built_in.audio_models.yue2.yue2_model import YuE2AudioModel
    from toolkit.config_modules import ModelConfig

    model_config = ModelConfig(**model_cfg)
    sd = YuE2AudioModel(device=device, model_config=model_config, dtype="bf16", noise_scheduler=None)
    sd.load_model()
    return sd


def attach_adapter(sd, network_cfg: dict, adapter_path: Path, device: str = "cpu"):
    """Build the same LoRASpecialNetwork the trainer builds and load the saved
    adapter into it; `load_weights` routes through
    `sd.convert_lora_weights_before_load` (yue2_model.py:795-802)."""
    import torch
    from toolkit.config_modules import NetworkConfig
    from toolkit.lora_special import LoRASpecialNetwork

    network_config = NetworkConfig(**network_cfg)
    network_kwargs = dict(network_config.network_kwargs or {})
    network_kwargs["target_lin_modules"] = sd.target_lora_modules
    unet = sd.get_model_to_train()
    network = LoRASpecialNetwork(
        text_encoder=sd.text_encoder,
        unet=unet,
        lora_dim=network_config.linear,
        multiplier=1.0,
        alpha=network_config.linear_alpha,
        train_unet=True,
        train_text_encoder=False,
        conv_lora_dim=network_config.conv,
        conv_alpha=network_config.conv_alpha,
        is_transformer=sd.is_transformer,
        base_model=sd,
        network_config=network_config,
        network_type=network_config.type,
        transformer_only=network_config.transformer_only,
        **network_kwargs,
    )
    network.force_to(torch.device(device), dtype=torch.float32)
    sd.network = network  # sets `_network`, which _ar_losses toggles for the KL base
    network._update_torch_multiplier()
    network.apply_to(sd.text_encoder, unet, False, True)
    network.can_merge_in = False
    network.load_weights(str(adapter_path))
    network.is_active = True
    network.multiplier = 1.0
    network.eval()
    return network


def _read_audio(path: Path):
    import torchaudio

    wav, sr = torchaudio.load(str(path))
    return wav, sr


def replay_item(sd, wav, sr, caption: str) -> Tuple[int, int, float, Optional[float], float, float]:
    """Run the per-item AR loss path. Returns
    (prefix_tokens, ar_target_tokens, ar_ce, ar_kl, tokenize_s, loss_s)."""
    import torch

    tokenizer = sd._get_semantic_tokenizer()
    t0 = time.perf_counter()
    tokens = tokenizer.tokenize(wav, sr)
    tokenize_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    prompt_embeds = sd.get_prompt_embeds(caption)
    prefix = sd._prefix_segment(prompt_embeds.text_embeds[0], prompt_embeds.attention_mask[0])
    prefix, abc = sd._item_prefix_and_abc(prefix, None, 0, caption)
    song = tokens.to(sd.device_torch)
    total = song.shape[0]
    limit = total if sd.ar_max_tokens <= 0 else min(total, sd.ar_max_tokens)
    ar_embeds, ar_ids = sd._ar_inputs(prefix, abc, song[:limit], end_token=limit == total)
    with torch.no_grad():
        ce, kl, _info = sd._ar_losses(ar_embeds, ar_ids, prefix, total, limit == total)
    loss_s = time.perf_counter() - t1
    return (
        int(prefix.shape[0]),
        int(ar_ids.shape[0]),
        float(ce.detach().float().item()),
        None if kl is None else float(kl.detach().float().item()),
        tokenize_s,
        loss_s,
    )


def run_replay(args) -> dict:
    model_cfg, network_cfg = load_config_sections(args.config)
    adapter = resolve_checkpoint(args.run_dir, args.checkpoint)
    pairs = list_val_pairs(args.val_dir)
    if args.limit is not None:
        pairs = pairs[: args.limit]

    print(f"[replay] checkpoint={args.checkpoint} adapter={adapter}", flush=True)
    print(f"[replay] val_dir={args.val_dir} pairs={len(pairs)} device={args.device}", flush=True)

    t_load = time.perf_counter()
    sd = build_model(model_cfg, args.ai_toolkit_dir, device=args.device)
    attach_adapter(sd, network_cfg, adapter, device=args.device)
    load_s = time.perf_counter() - t_load
    print(f"[replay] model+adapter loaded in {load_s:.1f}s", flush=True)

    results: List[ItemResult] = []
    for i, (stem, mp3, txt) in enumerate(pairs):
        caption = txt.read_text(encoding="utf-8")
        wav, sr = _read_audio(mp3)
        prefix_tok, target_tok, ce, kl, tokenize_s, loss_s = replay_item(sd, wav, sr, caption)
        res = ItemResult(
            index=i,
            stem=stem,
            caption_tokens=prefix_tok,
            ar_target_tokens=target_tok,
            ar_ce=ce,
            ar_kl=kl,
            tokenize_s=tokenize_s,
            loss_s=loss_s,
        )
        results.append(res)
        kl_txt = "None" if kl is None else f"{kl:.4f}"
        print(
            f"[{i + 1}/{len(pairs)}] {stem}  ar_ce={ce:.4f} ar_kl={kl_txt} "
            f"prefix={prefix_tok} targets={target_tok} "
            f"tokenize={tokenize_s:.2f}s loss={loss_s:.2f}s total={res.total_s:.2f}s",
            flush=True,
        )

    ce_mean, kl_mean = mean_losses(results)
    n = len(results)
    loss_mean = sum(r.loss_s for r in results) / n
    tok_mean = sum(r.tokenize_s for r in results) / n
    total_mean = sum(r.total_s for r in results) / n
    print(
        f"[replay] mean loss/ar_ce={ce_mean:.4f} "
        f"loss/ar_kl={'None' if kl_mean is None else f'{kl_mean:.4f}'}",
        flush=True,
    )
    print(
        f"[replay] per item: tokenize={tok_mean:.2f}s loss={loss_mean:.2f}s total={total_mean:.2f}s "
        f"(model load {load_s:.1f}s, not counted per item)",
        flush=True,
    )
    return {
        "checkpoint": args.checkpoint,
        "adapter": str(adapter),
        "val_dir": str(args.val_dir),
        "device": args.device,
        "n_items": n,
        "mean_ar_ce": ce_mean,
        "mean_ar_kl": kl_mean,
        "mean_tokenize_s": tok_mean,
        "mean_loss_s": loss_mean,
        "mean_total_s": total_mean,
        "model_load_s": load_s,
        "items": [
            {
                "stem": r.stem,
                "ar_ce": r.ar_ce,
                "ar_kl": r.ar_kl,
                "caption_tokens": r.caption_tokens,
                "ar_target_tokens": r.ar_target_tokens,
                "tokenize_s": r.tokenize_s,
                "loss_s": r.loss_s,
            }
            for r in results
        ],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--checkpoint", default="final", choices=sorted(CHECKPOINT_FILES), help="which pron checkpoint")
    p.add_argument("--limit", type=int, default=None, help="cap the number of val pairs (benchmark slice)")
    p.add_argument("--val-dir", type=Path, default=DEFAULT_VAL_DIR)
    p.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--ai-toolkit-dir", type=Path, default=DEFAULT_AI_TOOLKIT_DIR)
    p.add_argument("--device", default="cpu")
    p.add_argument("--out", type=Path, default=None, help="write the full results dict as JSON")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    results = run_replay(args)
    if args.out is not None:
        args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"[replay] wrote {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
