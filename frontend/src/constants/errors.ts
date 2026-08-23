// Centralised error messages (AC-M5.2: 14 error scenarios fully covered).
// Keyed by business error code (from dev plan §1.5) plus named UI scenarios.

export const ERROR_BY_CODE: Record<number, string> = {
  1001: '请求参数校验失败，请检查输入',
  2001: '目标错题本不存在，请刷新后重试',
  2002: '错题不存在，可能已被删除',
  3001: '不支持的图片格式，请上传 JPG/PNG/WEBP 格式',
  3002: '图片超过 10MB 限制，请压缩后重试',
  3003: '未识别到文字内容，请重新拍照或手动输入',
  4001: 'AI 服务暂时不可用，请稍后重试',
  5001: '当前没有需要复习的题目',
  5002: '复习会话已过期，请重新开始复习',
  9000: '服务器内部错误，请稍后重试',
}

// Named UI-level scenarios not tied to a single API code.
export const UI_ERRORS = {
  NO_NOTEBOOK_SELECTED: '请先选择一个错题本',
  NO_ERROR_SELECTED: '请至少勾选 1 道题再导入',
  EMPTY_QUESTION: '请输入题干内容',
  UNCHARGED_ANSWERS: '有题目尚未作答',
  NETWORK: '网络连接中断，请检查网络后重试',
  EXPORT_EMPTY: '该错题本还没有错题，暂无可导出的内容',
  SAVE_FAILED: '保存失败，请重试',
  VARIANT_FAILED: '变体题生成失败，请点击重试',
  STREAM_INTERRUPTED: '回答中断，已保留已输出的内容',
  DELETE_CONFIRM: '删除后数据将无法恢复，确认继续吗？',
  UPLOAD_FAILED: '图片上传失败，请重试或更换图片',
  CHAT_EMPTY: '请输入问题后再发送',
  NOTEBOOK_NAME_REQUIRED: '请填写错题本名称',
} as const

export function messageForCode(code: number): string {
  return ERROR_BY_CODE[code] || '请求失败，请稍后重试'
}
