"""
scripts/analysis_powerlaw.py

Derece dağılımı ve güç yasası (Power Law) analiz modülü:
- powerlaw paketi ile ampirik derece dizisine güç yasası fiti.
- Alpha (ölçek parametresi), xmin (minimum eşik) ve sigma tahmini.
- Alternatif dağılımlarla (üstel, log-normal, kesikli güç yasası) log-likelihood ratio testleri.
- Log-log grafiği (PDF ve CCDF) üretimi ve görselleştirme.
- Küçük örneklem ve model sınırlılıklarının bilimsel olarak belgelenmesi.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import networkx as nx
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Başsız (headless) ortamlar için
import matplotlib.pyplot as plt
import powerlaw

logger = logging.getLogger(__name__)


def fit_powerlaw_distribution(degrees: List[int], output_plot_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verilen derece dizisi için güç yasası uyumunu hesaplar ve
    üstel ile log-normal alternatif modellerle karşılaştırır.
    """
    deg_array = np.array([d for d in degrees if d > 0], dtype=float)
    if len(deg_array) < 10:
        raise ValueError(f"Güç yasası analizi için çok az düğüm ({len(deg_array)} düğüm).")

    # Kesikli (discrete) güç yasası fiti
    fit = powerlaw.Fit(deg_array, discrete=True, verbose=False)

    alpha = float(fit.power_law.alpha)
    xmin = float(fit.power_law.xmin)
    sigma = float(fit.power_law.sigma)

    # Karşılaştırma testleri: power_law vs exponential / lognormal / truncated_power_law
    # R: log-likelihood ratio. R > 0 ise power_law daha iyi, R < 0 ise alternatif daha iyi.
    # p: istatistiksel anlamlılık (p < 0.05 ise fark anlamlı, p >= 0.05 ise ayırt edilemez).
    r_exp, p_exp = fit.distribution_compare("power_law", "exponential", normalized_ratio=True)
    r_lognorm, p_lognorm = fit.distribution_compare("power_law", "lognormal", normalized_ratio=True)
    try:
        r_trunc, p_trunc = fit.distribution_compare("power_law", "truncated_power_law", normalized_ratio=True)
    except Exception as e:
        logger.warning(f"Truncated power law karşılaştırması yapılamadı: {e}")
        r_trunc, p_trunc = None, None

    # Bilimsel yorumlama kararı
    # Eğer p_lognorm >= 0.05 ise lognormal'e karşı üstünlüğü kanıtlanamamıştır.
    is_powerlaw_favored = bool(r_exp > 0 and p_exp < 0.05 and r_lognorm > 0 and p_lognorm < 0.05)

    interpretation = {
        "supports_pure_power_law": is_powerlaw_favored,
        "vs_exponential": {
            "R": float(r_exp),
            "p_value": float(p_exp),
            "favors": "power_law" if (r_exp > 0 and p_exp < 0.05) else ("exponential" if (r_exp < 0 and p_exp < 0.05) else "inconclusive")
        },
        "vs_lognormal": {
            "R": float(r_lognorm),
            "p_value": float(p_lognorm),
            "favors": "power_law" if (r_lognorm > 0 and p_lognorm < 0.05) else ("lognormal" if (r_lognorm < 0 and p_lognorm < 0.05) else "inconclusive")
        },
        "sample_size": len(deg_array),
        "nodes_above_xmin": int(np.sum(deg_array >= xmin)),
        "notes": (
            "Türkiye üniversiteler ağı (N=186 aktif üniversite), makro ölçekli küresel ağlara kıyasla "
            "küçük bir örneklem boyutu sergilemektedir. Derece aralığı sınırlıdır (k_min ve k_max dar bir banttadır). "
            "Bu nedenle log-normal ve üstel modellerle yapılan log-likelihood testlerinde p-değeri anlamlılık eşiğini "
            "aşamadığında saf bir güç yasası (scale-free) olduğunu iddia etmek bilimsel olarak yanıltıcıdır."
        )
    }

    results = {
        "alpha": alpha,
        "xmin": xmin,
        "sigma": sigma,
        "comparison": interpretation
    }

    # Çizim (Plotting)
    if output_plot_path:
        os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 1. CCDF (Tamamlayıcı Kümülatif Dağılım)
        fit.plot_ccdf(ax=ax1, color="navy", linewidth=2, label="Ampirik CCDF P(K ≥ k)")
        fit.power_law.plot_ccdf(ax=ax1, color="crimson", linestyle="--", label=f"Power Law Fit (α={alpha:.2f}, xmin={xmin:.0f})")
        fit.lognormal.plot_ccdf(ax=ax1, color="forestgreen", linestyle=":", label="Lognormal Fit")
        ax1.set_title("Derece CCDF (Log-Log Ölçek)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Derece (k)", fontsize=11)
        ax1.set_ylabel("P(K ≥ k)", fontsize=11)
        ax1.legend(loc="lower left", fontsize=10)
        ax1.grid(True, which="both", linestyle="--", alpha=0.5)

        # 2. PDF (Olasılık Yoğunluk Dağılımı)
        fit.plot_pdf(ax=ax2, color="navy", linewidth=2, label="Ampirik PDF P(k)")
        fit.power_law.plot_pdf(ax=ax2, color="crimson", linestyle="--", label=f"Power Law Fit")
        fit.lognormal.plot_pdf(ax=ax2, color="forestgreen", linestyle=":", label="Lognormal Fit")
        ax2.set_title("Derece PDF (Log-Log Ölçek)", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Derece (k)", fontsize=11)
        ax2.set_ylabel("P(k)", fontsize=11)
        ax2.legend(loc="lower left", fontsize=10)
        ax2.grid(True, which="both", linestyle="--", alpha=0.5)

        plt.suptitle("Türkiye Üniversiteleri Bilgisayar Bilimi Ağı: Derece Dağılımı ve Model Uyumu", fontsize=13, fontweight="bold", y=1.02)
        plt.tight_layout()
        plt.savefig(output_plot_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Güç yasası grafiği kaydedildi -> {output_plot_path}")

    return results
