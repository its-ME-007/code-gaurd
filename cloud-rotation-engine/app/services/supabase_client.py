"""
Supabase PostgreSQL database integration for incident audit logging.
Stores metadata about detected secrets (never raw credentials).
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

# Lazy import to avoid hard dependency on supabase-py
# Users must install: pip install supabase
try:
    import supabase
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase-py not installed. Supabase audit logging will be disabled.")


class SupabaseIncidentClient:
    """
    Client for logging detected secret incidents to a Supabase PostgreSQL database.
    Only metadata and secret hashes are stored; raw secrets are never transmitted.
    """
    
    TABLE_NAME = "secret_incidents"
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client for incident logging.
        
        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase API key (defaults to SUPABASE_KEY env var)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        self.enabled = SUPABASE_AVAILABLE and bool(self.url and self.key)
        
        if not self.enabled:
            logger.warning(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables to enable incident logging."
            )
            return
        
        try:
            self.client = supabase.create_client(self.url, self.key)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.enabled = False
    
    def log_detected_secret(
        self,
        secret_hash: str,
        secret_type: str,
        file_path: str,
        line_number: int,
        repo_name: str,
        risk_level: str,
        scan_id: str,
        detected_by: str,
        detected_at: Optional[datetime] = None,
    ) -> Dict:
        """
        Log a detected secret incident to the database.
        
        Args:
            secret_hash: SHA256 hash of the secret (never the raw secret)
            secret_type: Type of secret (aws, openai, github, etc.)
            file_path: File path where secret was found
            line_number: Line number in file
            repo_name: Repository name
            risk_level: Risk classification (critical, high, medium, low)
            scan_id: Batch scan identifier
            detected_by: Machine/agent that detected it
            detected_at: Detection timestamp (defaults to now)
            
        Returns:
            Dict with incident_id or error information
        """
        if not self.enabled:
            logger.debug("Supabase not enabled, skipping incident logging")
            return {"status": "skipped", "reason": "Supabase not configured"}
        
        try:
            incident_id = str(uuid4())
            detected_at = detected_at or datetime.utcnow()
            
            incident_record = {
                "incident_id": incident_id,
                "scan_id": scan_id,
                "repo_name": repo_name,
                "file_path": file_path,
                "line_number": line_number,
                "secret_type": secret_type,
                "secret_hash": secret_hash,
                "risk_level": risk_level,
                "detected_by": detected_by,
                "detected_at": detected_at.isoformat(),
                "remediation_status": "pending",
            }
            
            response = self.client.table(self.TABLE_NAME).insert(incident_record).execute()
            
            logger.info(f"Logged incident {incident_id} for {secret_type} in {repo_name}")
            return {"status": "success", "incident_id": incident_id}
            
        except Exception as e:
            logger.error(f"Failed to log incident to Supabase: {e}")
            return {"status": "error", "reason": str(e)}
    
    def log_batch_secrets(
        self,
        scan_id: str,
        repo_name: str,
        detected_by: str,
        secrets: List[Dict],
    ) -> Dict:
        """
        Log multiple detected secrets in a single batch operation.
        Improves performance and scan tracking.
        
        Args:
            scan_id: Unique identifier for this scan batch
            repo_name: Repository name
            detected_by: Machine/agent performing the scan
            secrets: List of detected secrets with structure:
                [
                    {
                        "secret_type": "aws",
                        "secret_hash": "hash_value",
                        "file_path": "app/config.py",
                        "line_number": 18,
                        "risk_level": "critical"
                    },
                    ...
                ]
            
        Returns:
            Dict with processing summary
        """
        if not self.enabled:
            logger.debug("Supabase not enabled, skipping batch logging")
            return {"status": "skipped", "incidents_logged": 0, "reason": "Supabase not configured"}
        
        try:
            incidents_logged = 0
            duplicates_detected = 0
            errors = []
            
            for secret in secrets:
                # Check for duplicate
                existing = self._check_duplicate_hash(secret["secret_hash"], repo_name)
                
                if existing:
                    duplicates_detected += 1
                    logger.debug(f"Duplicate secret hash detected: {secret['secret_hash'][:8]}...")
                    continue
                
                # Log new incident
                result = self.log_detected_secret(
                    secret_hash=secret["secret_hash"],
                    secret_type=secret.get("secret_type", "unknown"),
                    file_path=secret["file_path"],
                    line_number=secret["line_number"],
                    repo_name=repo_name,
                    risk_level=secret.get("risk_level", "medium"),
                    scan_id=scan_id,
                    detected_by=detected_by,
                )
                
                if result.get("status") == "success":
                    incidents_logged += 1
                else:
                    errors.append(result.get("reason", "Unknown error"))
            
            return {
                "status": "success" if incidents_logged > 0 else "partial",
                "scan_id": scan_id,
                "incidents_logged": incidents_logged,
                "duplicates_detected": duplicates_detected,
                "errors": errors if errors else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to process batch secrets: {e}")
            return {"status": "error", "reason": str(e)}
    
    def _check_duplicate_hash(self, secret_hash: str, repo_name: str) -> bool:
        """
        Check if a secret hash already exists in the database.
        
        Args:
            secret_hash: SHA256 hash to check
            repo_name: Repository name for scoping
            
        Returns:
            True if duplicate found, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            response = self.client.table(self.TABLE_NAME)\
                .select("incident_id")\
                .eq("secret_hash", secret_hash)\
                .eq("repo_name", repo_name)\
                .limit(1)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.warning(f"Error checking for duplicate hash: {e}")
            return False
    
    def update_remediation_status(
        self,
        incident_id: str,
        status: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Update the remediation status of an incident.
        
        Args:
            incident_id: The incident UUID
            status: New status (pending, resolved, skipped, failed)
            metadata: Optional metadata dict to update with status
            
        Returns:
            Dict with operation result
        """
        if not self.enabled:
            return {"status": "skipped", "reason": "Supabase not configured"}
        
        try:
            update_data = {"remediation_status": status}
            if metadata:
                update_data.update(metadata)
            
            self.client.table(self.TABLE_NAME)\
                .update(update_data)\
                .eq("incident_id", incident_id)\
                .execute()
            
            logger.info(f"Updated incident {incident_id} status to {status}")
            return {"status": "success", "incident_id": incident_id}
            
        except Exception as e:
            logger.error(f"Failed to update incident status: {e}")
            return {"status": "error", "reason": str(e)}
    
    def get_incidents_by_repo(self, repo_name: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve incidents for a specific repository.
        
        Args:
            repo_name: Repository name to filter by
            limit: Maximum number of incidents to return
            
        Returns:
            List of incident records
        """
        if not self.enabled:
            return []
        
        try:
            response = self.client.table(self.TABLE_NAME)\
                .select("*")\
                .eq("repo_name", repo_name)\
                .order("detected_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to retrieve incidents for {repo_name}: {e}")
            return []
    
    def get_pending_incidents(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve all pending (unresolved) incidents.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of pending incident records
        """
        if not self.enabled:
            return []
        
        try:
            response = self.client.table(self.TABLE_NAME)\
                .select("*")\
                .eq("remediation_status", "pending")\
                .order("detected_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to retrieve pending incidents: {e}")
            return []
