"""
.. _models-beam:

Particle Beam Models
--------------------

Module with ``pydantic`` models to validate and store
data structures relative to particle beams.
"""

from math import sqrt

from pydantic import BaseModel


class BeamParameters(BaseModel):
    """
    .. versionadded:: 0.12.0

    Class to encompass, validate and manipulate properties of a
    particle beam. One can find a usage example in the :ref:`beam
    enveloppe demo <demo-beam-enveloppe>`.
    """

    pc_GeV: float | None = None  # Beam momentum in [GeV]  # noqa: N815
    E_0_GeV: float | None = 0.9382720813  # Particle rest mass energy in [GeV], defaults to that of a proton
    charge: float | None = 1  # Particle charge in in [e], defaults to that of a proton
    nemitt_x: float | None = None  # Horizontal normalized emittance in [m]
    nemitt_y: float | None = None  # Vertical normalized emittance in [m]
    deltap_p: float | None = None  # Momentum deviation

    @property
    def B_rho_Tm(self) -> float:  # noqa: N802
        """Beam rigidity in [T/m]."""
        return self.pc_GeV / 0.3

    @property
    def E_tot_GeV(self) -> float:  # noqa: N802
        """Total beam energy in [GeV]."""
        return sqrt(self.pc_GeV**2 + self.E_0_GeV**2)

    @property
    def E_kin_GeV(self) -> float:  # noqa: N802
        """Total beam energy in [GeV]."""
        return self.E_tot_GeV - self.E_0_GeV

    @property
    def gamma_rel(self) -> float:
        """Relativistic gamma."""
        return self.E_tot_GeV / self.E_0_GeV

    @property
    def beta_rel(self) -> float:
        """Relativistic beta."""
        return self.pc_GeV / sqrt(self.pc_GeV**2 + self.E_0_GeV**2)

    @property
    def gemitt_x(self) -> float:
        """Horizontal geometric emittance in [m]."""
        return self.nemitt_x / (self.gamma_rel / self.beta_rel)

    @property
    def gemitt_y(self) -> float:
        """Vertical geometric emittance in [m]."""
        return self.nemitt_y / (self.gamma_rel / self.beta_rel)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return (
            f"Beam Parameters for particle of charge {self.charge} \n"
            f"Beam momentum = {self.pc_GeV:2.3f} GeV/c \n"
            f"Normalized x-emittance = {self.nemitt_x * 1e6:2.3f} mm mrad \n"  # 1e-6 -> 1e-3 in m and 1e-3 in rad
            f"Normalized y-emittance = {self.nemitt_y * 1e6:2.3f} mm mrad \n"  # 1e-6 -> 1e-3 in m and 1e-3 in rad
            f"Momentum deviation deltap/p = {self.deltap_p} \n"
            f"  -> Beam total energy = {self.E_tot_GeV:2.3f} GeV \n"
            f"  -> Beam kinetic energy = {self.E_kin_GeV:2.3f} GeV \n"
            f"  -> Beam rigidity = {self.B_rho_Tm:2.3f} Tm \n"
            f"  -> Relativistic beta = {self.beta_rel:2.5f} \n"
            f"  -> Relativistic gamma = {self.gamma_rel:2.3f} \n"
            f"  -> Geometrical x emittance = {self.nemitt_x * 1e6:2.3f} mm mrad \n"  # 1e-6 -> 1e-3 in m and 1e-3 in rad
            f"  -> Geometrical y emittance = {self.gemitt_y * 1e6:2.3f} mm mrad \n"  # 1e-6 -> 1e-3 in m and 1e-3 in rad
        )
