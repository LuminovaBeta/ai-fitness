import { request } from './http'

export const loginByAccount = (payload) => {
  return request('/api/auth/login/', {
    method: 'POST',
    body: payload
  })
}

export const loginByFace = (faceData) => {
  return request('/api/auth/face-login/', {
    method: 'POST',
    body: { face_data: faceData }
  })
}

export const registerFace = (faceData) => {
  return request('/api/auth/face-register/', {
    method: 'POST',
    auth: true,
    body: { face_data: faceData }
  })
}

export const registerAccount = (payload) => {
  return request('/api/auth/register/', {
    method: 'POST',
    body: payload
  })
}
