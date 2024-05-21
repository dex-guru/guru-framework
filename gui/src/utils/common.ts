export const getShortAddress = (address?: string, count = 4): string => {
  const charCount = Math.max(count, 4)

  const regexp = new RegExp(`(0x)([0-9a-f]{${charCount - 1}})(.+)([0-9a-f]{${charCount}})`, 'i')

  const result = `${address}`.replace(regexp, '$1$2…$4')
  return result
}
