"""Service layer for Kubernetes pod listing and context collection."""
import logging
import os
from typing import TypedDict
from kubernetes import client
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import MaxRetryError, ReadTimeoutError
from backend.models.schemas import PodInfo, PodListResponse
from backend.utils import PodNotFoundError

logger = logging.getLogger(__name__)

_K8S_LIST_TIMEOUT = int(os.getenv("K8S_LIST_TIMEOUT", "30"))   # seconds – used for pod/event list calls
_K8S_READ_TIMEOUT = int(os.getenv("K8S_READ_TIMEOUT", "15"))   # seconds – used for single-object reads
_K8S_LOG_TIMEOUT = int(os.getenv("K8S_LOG_TIMEOUT", "20"))     # seconds – used for log streaming


class PodContext(TypedDict):
    """Pod diagnostic context collected from the Kubernetes API."""

    pod_name: str
    namespace: str
    describe: str
    logs: str
    error_type: str


class PodService:
    """Provides high-level operations for querying Kubernetes pod data."""

    def __init__(self) -> None:
        self._v1: client.CoreV1Api | None = None

    def _get_v1(self) -> client.CoreV1Api:
        """Return a cached CoreV1Api client, creating it on first use."""
        if self._v1 is None:
            self._v1 = client.CoreV1Api()
        return self._v1

    def list_pods(self, namespace: str | None = None) -> PodListResponse:
        """List all pods, optionally filtered by namespace."""
        v1 = self._get_v1()
        try:
            if namespace:
                pods = v1.list_namespaced_pod(
                    namespace=namespace, watch=False, _request_timeout=_K8S_LIST_TIMEOUT
                )
            else:
                pods = v1.list_pod_for_all_namespaces(
                    watch=False, _request_timeout=_K8S_LIST_TIMEOUT
                )
        except (ReadTimeoutError, MaxRetryError) as e:
            logger.warning("K8s API timed out listing pods: %s", e)
            return PodListResponse(pods=[], total=0)
        except ApiException as e:
            logger.warning("K8s API error listing pods: HTTP %s – %s", e.status, e.reason)
            return PodListResponse(pods=[], total=0)
        except Exception as e:
            logger.error("Unexpected error listing pods: %s", e)
            return PodListResponse(pods=[], total=0)

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

    def get_pod_context(self, pod_name: str, namespace: str = "default") -> PodContext:
        """Collect describe output and recent logs for a pod."""
        v1 = self._get_v1()
        context = PodContext(
            pod_name=pod_name,
            namespace=namespace,
            describe="",
            logs="",
            error_type="Unknown",
        )

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
                    break
                elif cs.state.terminated and cs.state.terminated.reason not in (None, "Completed"):
                    error_type = cs.state.terminated.reason or "Terminated"
                    break
            if error_type == "Unknown" and phase == "Pending":
                error_type = "Pending"

            context["error_type"] = error_type

            # Build describe-like summary
            events = v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod_name}",
                _request_timeout=_K8S_LIST_TIMEOUT,
            )
            event_lines = [f"{e.reason}: {e.message}" for e in events.items[-10:]]
            context["describe"] = (
                f"Phase: {phase}\nContainerStatuses: {container_statuses}\nEvents:\n"
                + "\n".join(event_lines)
            )

        except (ReadTimeoutError, MaxRetryError) as e:
            logger.warning("K8s API timed out describing pod %s/%s: %s", namespace, pod_name, e)
            context["describe"] = f"K8s API timed out while describing pod (limit={_K8S_READ_TIMEOUT}s): {e}"
        except ApiException as e:
            if e.status == 404:
                raise PodNotFoundError(pod_name, namespace) from e
            logger.warning("K8s API error describing pod %s/%s: HTTP %s", namespace, pod_name, e.status)
            context["describe"] = f"K8s API error ({e.status}): {e.reason}"
        except Exception as e:
            logger.error("Unexpected error describing pod %s/%s: %s", namespace, pod_name, e)
            context["describe"] = f"Could not describe pod: {e}"

        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, tail_lines=100, _request_timeout=_K8S_LOG_TIMEOUT
            )
            context["logs"] = logs
        except (ReadTimeoutError, MaxRetryError) as e:
            logger.warning("K8s API timed out fetching logs for %s/%s: %s", namespace, pod_name, e)
            context["logs"] = f"K8s API timed out fetching logs (limit={_K8S_LOG_TIMEOUT}s): {e}"
        except ApiException as e:
            logger.warning("K8s API error fetching logs for %s/%s: HTTP %s", namespace, pod_name, e.status)
            context["logs"] = f"K8s API error fetching logs ({e.status}): {e.reason}"
        except Exception as e:
            logger.error("Unexpected error fetching logs for %s/%s: %s", namespace, pod_name, e)
            context["logs"] = f"Could not retrieve logs: {e}"

        return context
