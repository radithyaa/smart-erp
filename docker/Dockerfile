# Build an ERPNext bench image FROM the cloned submodule sources.
#
# This repo tracks Frappe + ERPNext as git submodules under ./apps (pinned to
# the stable `version-16` branch, which ships the Vue-based frappe-ui frontend),
# so we build from source instead of using the prebuilt frappe/erpnext image.
# Editing apps/frappe or apps/erpnext and rebuilding is what makes teammates
# see each other's code changes:
#
#     ./scripts/smart-erp.sh build && ./scripts/smart-erp.sh up -d
#
# L2 APP (`apps/smart_erp_ai`) — AGENT-RULES layer rules:
#   * `apps/smart_erp_ai` is OUR app (L2, product code). It is a plain directory
#     (NOT a submodule), so it lives in this repo and is copied into the image.
#   * L1 (`apps/frappe`, `apps/erpnext`) stays read-only/upstream; never edit it.
#
# VERSION PINNING (keep these in sync, see .gitmodules):
#   * Base image `frappe/erpnext:v16` matches the submodule branch `version-16`.
#   * Do NOT point the submodules back at `develop` (that is 17-dev/unstable and
#     mismatches this v16 base image). To move up, bump BOTH the branch in
#     .gitmodules AND this base image tag together.

FROM frappe/erpnext:v16

USER root

# Copy only the app source trees. node_modules from the base image would be
# shadowed/removed by a full COPY, so we reinstall JS deps afterwards.
COPY --chown=frappe:frappe apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --chown=frappe:frappe apps/erpnext /home/frappe/frappe-bench/apps/erpnext
# L2 product app (ours). No node_modules to preserve; Python-only for now.
COPY --chown=frappe:frappe apps/smart_erp_ai /home/frappe/frappe-bench/apps/smart_erp_ai

USER frappe
WORKDIR /home/frappe/frappe-bench

# Reinstall JS deps for the freshly copied sources so the asset pipeline works.
RUN cd apps/frappe && yarn install --frozen-lockfile && \
    cd ../erpnext && yarn install --frozen-lockfile

# Register the L2 app so `bench` can import it:
#   * editable install creates env/.../smart_erp_ai.pth pointing at apps/smart_erp_ai
#     (this is what makes `bench execute`/`bench console` resolve the module),
#   * apps.txt lists the app for the bench (also synced into sites/ at runtime).
# NOTE: sites/apps.txt may lack a trailing newline, so we append via Python to
# avoid gluing the new name onto the last line (a real failure mode we hit once).
RUN env/bin/pip install -e apps/smart_erp_ai
RUN env/bin/python -c "\
import pathlib; \
p = pathlib.Path('sites/apps.txt'); \
text = p.read_text() if p.exists() else ''; \
apps = [a for a in text.splitlines() if a.strip()]; \
p.write_text(''.join(a + chr(10) for a in dict.fromkeys(apps + ['smart_erp_ai'])))"

# Rebuild front-end assets from the copied sources.
RUN bench build --app frappe && bench build --app erpnext
