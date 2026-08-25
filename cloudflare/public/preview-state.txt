const actionableStatuses = new Set(["ACKNOWLEDGED", "RECONCILIATION_REQUIRED"]);

export function selectTrackedClosePreview(previews) {
  return previews.find((preview) => actionableStatuses.has(preview.status))
    ?? previews.find((preview) => preview.status === "CREATED")
    ?? null;
}
