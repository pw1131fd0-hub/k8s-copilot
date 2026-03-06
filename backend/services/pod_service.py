"""Service layer for Kubernetes pod listing and context collection."""
from typing import Optional
from kubernetes import client
from backend.models.schemas import PodInfo, PodListResponse

_K8S_LIST_TIMEOUT = 30   # seconds – used for pod/event list calls
_K8S_READ_TIMEOUT = 15   # seconds – used for single-object reads
_K8S_LOG_TIMEOUT = 20    # seconds – used for log streaming


class PodService:
    """Provides high-level operations for querying Kubernetes pod data."""

    def list_pods(self, namespace: Optional[str] = None) -> PodListResponse:
        """List all pods, optionally filtered by namespace."""
        v1 = client.CoreV1Api()
        if namespace:
            pods = v1.list_namespaced_pod(
                namespace=namespace, watch=False, _request_timeout=_K8S_LIST_TIMEOUT
            )
        else:
            pods = v1.list_pod_for_all_namespaces(
                watch=False, _request_timeout=_K8S_LIST_TIMEOUT
            )

        pod_list = []
        for item in pods.items:
            conditions = []
            if item.status.conditions:
                conditions = [
                    {"type": c.type, "status": c.status}
                    for c in item.status.conditions
                ]
            pod_list.append(PodInfo(
                name=item.metadata.name,
                namespace=item.metadata.namespace,
                status=item.status.phase,
                ip=item.status.pod_ip,
                conditions=conditions,
            ))

        return PodListResponse(pods=pod_list, total=len(pod_list))

    def get_pod_context(self, pod_name: str, namespace: str = "default") -> dict:
        """Collect describe output and recent logs for a pod."""
        v1 = client.CoreV1Api()
        context = {"pod_name": pod_name, "namespace": namespace, "describe": "", "logs": "", "error_type": "Unknown"}

        try:
            pod = v1.read_namespaced_pod(
                name=pod_name, namespace=namespace, _request_timeout=_K8S_READ_TIMEOUT
            )
            phase = pod.status.phase
            container_statuses = pod.status.container_statuses or []

            error_type = "Unknown"
            for cs in container_statuses:
                if cs.state.waiting:
                    error_type = cs.state.waiting.reason or "Waiting"
                elif cs.state.terminated:
                    error_type = cs.state.terminated.reason or "Terminated"
            if phase == "Pending":
                error_type = "Pending"

            context["error_type"] = error_type

            # Build describe-like summary
            events = v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod_name}",
                _request_timeout=_K8S_LIST_TIMEOUT,
            )
            event_lines = [f"{e.reason}: {e.message}" for e in events.items[-10:]]
            context["describe"] = f"Phase: {phase}\nContainerStatuses: {container_statuses}\nEvents:\n" + "\n".join(event_lines)

        except Exception as e:
            context["describe"] = f"Could not describe pod: {e}"

        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, tail_lines=100, _request_timeout=_K8S_LOG_TIMEOUT
            )
            context["logs"] = logs
        except Exception as e:
            context["logs"] = f"Could not retrieve logs: {e}"

        return context
