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

USER frappe
WORKDIR /home/frappe/frappe-bench

# Reinstall JS deps for the freshly copied sources so the asset pipeline works.
RUN cd apps/frappe && yarn install --frozen-lockfile && \
    cd ../erpnext && yarn install --frozen-lockfile

# Rebuild front-end assets from the copied sources.
RUN bench build --app frappe && bench build --app erpnext
