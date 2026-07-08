import { request } from './http'

export const askAi = (message) => {
  return request('/api/chat/ask/', {
    method: 'POST',
    auth: true,
    body: { message }
  })
}
