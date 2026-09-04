"""
Wrapper around the contact-angle PCA calculator for use in the pipeline.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'contact-angle'))
from contact_angle_pca import ContactAngleCalculator


def compute_contact_angle(txt_file_path: str,
                          output_dir: str = None,
                          z_threshold: float = 0.05,
                          k_neighbors: int = 30,
                          min_points: int = 10) -> float:
    """
    Compute the contact angle from a COMSOL simulation output TXT file.

    Args:
        txt_file_path: path to the point-cloud TXT file
        output_dir: optional directory for visualization output
        z_threshold: contact-line threshold (z < this value)
        k_neighbors: number of neighbors for PCA
        min_points: minimum contact-line points

    Returns:
        Contact angle in degrees.
    """
    calc = ContactAngleCalculator(
        z_threshold=z_threshold,
        k_neighbors=k_neighbors,
        min_points=min_points,
    )
    angle = calc.run(txt_file_path, output_dir)
    return angle
