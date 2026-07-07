# AdProof — Backblaze B2 Storage

Content-addressable storage with provenance guarantees. One bucket, prefix-partitioned.

---

## 1. Bucket

| Setting | Value |
|---------|-------|
| Name | `adproof-assets` (or `B2_BUCKET_NAME` env) |
| Type | S3-compatible API via `genblaze_s3.S3StorageBackend.for_backblaze()` |
| Setup script | `infra/b2-bucket-setup.py` |

---

## 2. Key Layout

```
adproof-assets/
├── briefs/{brief_id}/
│   └── reference-image.{ext}
├── runs/{run_id}/
│   ├── steps/
│   │   ├── storyboard/{step_id}.png
│   │   ├── storyboard/{step_id}.manifest.json
│   │   ├── animate/{model_name}/{step_id}.mp4
│   │   ├── animate/{model_name}/{step_id}.manifest.json
│   │   ├── voiceover/{step_id}.mp3
│   │   ├── voiceover/{step_id}.manifest.json
│   │   ├── score/{step_id}.mp3
│   │   └── score/{step_id}.manifest.json
│   ├── variants/{variant_id}/
│   │   ├── final.mp4
│   │   ├── thumbnail.jpg
│   │   └── manifest.json         # rolled-up, SHA-256, replayable
│   └── run.manifest.json         # top-level, references all step manifests
└── logs/{run_id}/pipeline.log
```

### Key Builder Functions

Implemented in `apps/worker/storage/key_layout.py`:

```python
brief_reference_key(brief_id: str, ext: str) -> str
step_asset_key(run_id, step_name, step_id, ext, model=None) -> str
step_manifest_key(run_id, step_name, step_id, model=None) -> str
variant_final_key(run_id, variant_id) -> str
variant_thumbnail_key(run_id, variant_id) -> str
variant_manifest_key(run_id, variant_id) -> str
run_manifest_key(run_id) -> str
pipeline_log_key(run_id) -> str
```

---

## 3. B2 Features to Wire Up

Judges are told to look for these. All must be configured.

### 3.1 Object Lock

- **Target:** Every `*.manifest.json` file
- **Mode:** Governance
- **Minimum retention:** 30 days
- **Purpose:** Tamper-evident provenance — manifests cannot be deleted or overwritten during retention period

Configured in `infra/b2-bucket-setup.py` and enforced on upload in `storage/b2_client.py`.

### 3.2 Lifecycle Rules

| Rule | Prefix | Action | Retention |
|------|--------|--------|-----------|
| Delete intermediates | `runs/*/steps/` | Auto-delete after **7 days** | Temporary pipeline artifacts |
| Keep forever | `runs/*/variants/` | No expiration | Final outputs |
| Keep forever | `**/*.manifest.json` | No expiration | Provenance records |
| Keep forever | `briefs/` | No expiration | User uploads |

Implemented in `storage/lifecycle_rules.py`, applied via setup script.

### 3.3 Event Notifications

- **Trigger:** `PutObject` on `variants/*/final.mp4`
- **Destination:** `https://<vercel-domain>/api/webhooks/b2`
- **Purpose:** Flip brief status to `done` and push SSE update to frontend (no polling)

Flow:

```
Worker uploads final.mp4 to B2
       │
       ▼
B2 Event Notification → POST /api/webhooks/b2
       │
       ▼
Webhook handler → update brief status → SSE broadcast
       │
       ▼
Frontend PipelineStatusStream → VariantGrid renders
```

---

## 4. Upload Conventions

| Asset Type | Content-Type | Object Lock |
|------------|--------------|-------------|
| PNG keyframes | `image/png` | No |
| MP4 clips | `video/mp4` | No |
| MP3 audio | `audio/mpeg` | No |
| JPG thumbnails | `image/jpeg` | No |
| manifest.json | `application/json` | **Yes** (governance, 30d) |
| pipeline.log | `text/plain` | No |

---

## 5. Signed URLs

Backend generates pre-signed URLs for frontend download/preview:

- `GET /runs/{id}/manifest` → signed URL to `variant manifest.json`
- Variant thumbnails served via signed URL (short TTL, e.g. 1 hour)

Never expose B2 credentials to the frontend.

---

## 6. Verification

`GET /runs/{id}/verify`:

1. Download `variants/{variant_id}/manifest.json` from B2
2. Read claimed SHA-256 from manifest
3. Download `final.mp4`, compute SHA-256
4. Return `{ match: true/false, expected, actual }`

Object Lock ensures the manifest hasn't been tampered with since upload.

---

## 7. Environment Variables

```env
B2_KEY_ID=your_application_key_id
B2_APP_KEY=your_application_key
B2_BUCKET_NAME=adproof-assets
B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com  # region-specific
```

---

## 8. Free Tier Notes (Hackathon)

Backblaze B2 free tier: **10 GB storage**, 1 GB download/day.

- Lifecycle rule deleting `steps/` after 7 days keeps storage lean
- Thumbnails are small; final MP4s are the main storage cost
- Manifests are tiny (JSON, few KB each)

---

## 9. Setup Checklist

- [ ] Run `python infra/b2-bucket-setup.py`
- [ ] Verify Object Lock enabled on bucket
- [ ] Verify lifecycle rules in B2 console
- [ ] Configure event notification pointing to Vercel webhook URL
- [ ] Test upload + manifest Object Lock via pipeline isolation script
- [ ] Test webhook fires on `final.mp4` PUT
