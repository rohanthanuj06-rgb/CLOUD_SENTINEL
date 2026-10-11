import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.config import settings
from app.models.alert import AlertModel
from app.models.recovery import RecoveryActionModel
from app.models.audit import AuditLogEntry

logger = logging.getLogger("cloudsentinel.firebase")


class FirebaseService:
    def __init__(self):
        self.is_connected = False
        self.db = None
        self._init_firebase()

    def _init_firebase(self):
        if not settings.FIREBASE_PROJECT_ID:
            logger.info("Firebase Project ID not set. Operating in Local Demo Mode.")
            return

        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                if settings.FIREBASE_CLIENT_EMAIL and settings.FIREBASE_PRIVATE_KEY:
                    # Initialize using service account info
                    cred_dict = {
                        "type": "service_account",
                        "project_id": settings.FIREBASE_PROJECT_ID,
                        "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
                        "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    }
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                else:
                    firebase_admin.initialize_app()

            self.db = firestore.client()
            self.is_connected = True
            logger.info(f"Connected to Firebase Firestore for project: {settings.FIREBASE_PROJECT_ID}")
        except Exception as e:
            logger.warning(f"Could not initialize Firebase Firestore: {e}. Falling back to Local Demo Mode.")
            self.is_connected = False

    async def save_aggregated_metrics(self, aggregated_records: List[Dict[str, Any]]):
        """Batches aggregated metrics to Firestore collection 'metrics'"""
        if not self.is_connected or not self.db:
            return

        def _sync_write():
            batch = self.db.batch()
            for record in aggregated_records[:50]:  # Firestore limit is 500 per batch
                doc_ref = self.db.collection("metrics").document()
                batch.set(doc_ref, record)
            batch.commit()

        try:
            await asyncio.to_thread(_sync_write)
            logger.info(f"Batched {len(aggregated_records)} aggregated metric records to Firestore.")
        except Exception as e:
            logger.error(f"Failed to batch metrics to Firestore: {e}")

    async def record_alert(self, alert: AlertModel):
        if not self.is_connected or not self.db:
            return

        def _sync_write():
            doc_ref = self.db.collection("alerts").document(alert.id)
            doc_ref.set(alert.model_dump())

        try:
            await asyncio.to_thread(_sync_write)
        except Exception as e:
            logger.error(f"Failed to save alert to Firestore: {e}")

    async def record_recovery(self, recovery: RecoveryActionModel):
        if not self.is_connected or not self.db:
            return

        def _sync_write():
            doc_ref = self.db.collection("recovery_actions").document(recovery.recovery_id)
            doc_ref.set(recovery.model_dump())

        try:
            await asyncio.to_thread(_sync_write)
        except Exception as e:
            logger.error(f"Failed to save recovery action to Firestore: {e}")

    async def record_audit(self, audit: AuditLogEntry):
        if not self.is_connected or not self.db:
            return

        def _sync_write():
            doc_ref = self.db.collection("audit_logs").document(audit.id)
            doc_ref.set(audit.model_dump())

        try:
            await asyncio.to_thread(_sync_write)
        except Exception as e:
            logger.error(f"Failed to save audit log to Firestore: {e}")


firebase_service = FirebaseService()
