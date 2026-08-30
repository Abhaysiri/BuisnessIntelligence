from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user

from app.schemas.agent import AgentResponse
from app.schemas.agent_run import AgentRunResponse
from app.schemas.agent_finding import AgentFindingResponse
from app.schemas.finding_evidence import FindingEvidenceResponse
from app.schemas.driver_candidate import DriverCandidateResponse

from app.services.agent_service import AgentService


router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


@router.get(
    "/",
    response_model=list[AgentResponse]
)
def get_agents(
    current_user: dict = Depends(get_current_user)
):
    return AgentService.get_agents()


@router.get(
    "/runs/{investigation_id}",
    response_model=list[AgentRunResponse]
)
def get_agent_runs(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    return AgentService.get_runs(investigation_id)


@router.get(
    "/runs/{agent_run_id}/findings",
    response_model=list[AgentFindingResponse]
)
def get_agent_findings(
    agent_run_id: str,
    current_user: dict = Depends(get_current_user)
):
    return AgentService.get_findings(agent_run_id)


@router.get(
    "/findings/{finding_id}/evidence",
    response_model=list[FindingEvidenceResponse]
)
def get_finding_evidence(
    finding_id: str,
    current_user: dict = Depends(get_current_user)
):
    return AgentService.get_evidence(finding_id)


@router.get(
    "/investigations/{investigation_id}/drivers",
    response_model=list[DriverCandidateResponse]
)
def get_driver_candidates(
    investigation_id: str,
    current_user: dict = Depends(get_current_user)
):
    return AgentService.get_driver_candidates(investigation_id)