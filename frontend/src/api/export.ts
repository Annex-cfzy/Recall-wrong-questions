// Export endpoints return files (not the JSON envelope), so we trigger a
// browser download directly against the dev-proxied /api path.
function triggerDownload(url: string) {
  const a = document.createElement('a')
  a.href = url
  a.setAttribute('download', '')
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

export function exportPdf(notebookId: number, includeAnswer = true) {
  triggerDownload(`/api/export/pdf/${notebookId}?include_answer=${includeAnswer}`)
}

export function exportMarkdown(notebookId: number, includeAnswer = true) {
  triggerDownload(`/api/export/markdown/${notebookId}?include_answer=${includeAnswer}`)
}
