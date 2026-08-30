from app.repositories.kpi_repository import KPIRepository


class KPIService:

    @staticmethod
    def get_kpis():
        return KPIRepository.get_all()

    @staticmethod
    def get_kpi(kpi_id: str):
        return KPIRepository.get_by_id(kpi_id)

    @staticmethod
    def get_kpi_versions(kpi_id: str):
        return KPIRepository.get_versions(kpi_id)

    @staticmethod
    def get_kpi_measurements(kpi_id: str):
        return KPIRepository.get_measurements(kpi_id)