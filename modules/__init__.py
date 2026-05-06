# Modules package initialization
from .auth import AuthModule
from .patient import PatientModule
from .doctor import DoctorModule
from .appointment import AppointmentModule
from .billing import BillingModule
from .pharmacy import PharmacyModule
from .labtest import LabTestModule

__all__ = [
    'AuthModule',
    'PatientModule',
    'DoctorModule', 
    'AppointmentModule',
    'BillingModule',
    'PharmacyModule',
    'LabTestModule'
]