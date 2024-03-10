#!/usr/bin/env bash
set -exo pipefail

helm upgrade --install frontstage-pricem _infra/helm/frontstage
