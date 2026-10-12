# Build an ERPNext bench image FROM the cloned submodule sources.
#
# Option B (this repo) tracks Frappe + ERPNext as git submodules under ./apps,
# so we build from source instead of using the prebuilt frappe/erpnext image.
# Editing apps/frappe or apps/erpnext and rebuilding is what makes teammates
# see each other's code changes:
#
#     ./scripts/smart-erp.sh build && ./scripts/smart-erp.sh up -d
#
# The base image already ships Python 3.14, Node 24, wkhtmltopdf and a bench
# skeleton at /home/frappe/frappe-bench, matching what `develop` requires.

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
