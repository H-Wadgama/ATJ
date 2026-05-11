"""
Standalone entry-point for the ETJ (Ethanol-to-Jet) system.

Mirrors the rcf_4_21_2026 pattern: call create_etj_system() with an optional
pre-built ethanol stream (ins) and/or SAF production target (req_saf, MM gal/yr).

Usage:
    python -m atj_saf.atj_bst.etj_run

When integrating downstream of cellulosic ethanol production, pass the ethanol
stream directly:
    from atj_saf.atj_bst.etj_system import create_etj_system
    etj_sys = create_etj_system(ins=F.Ethanol_Out, req_saf=9)
"""
from atj_saf.atj_bst.etj_system import create_etj_system

etj_sys = create_etj_system(req_saf=9)
etj_sys.simulate()
etj_sys.show()
