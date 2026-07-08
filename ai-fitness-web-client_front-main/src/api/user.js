import { request } from './http'

export const fetchDashboard = () => {
  return request('/api/user/dashboard/', { auth: true })
}

export const fetchUserActivities = () => {
  return request('/api/user/activities/', { auth: true })
}

export const fetchUserActivityDetail = (id) => {
  return request(`/api/user/activities/${id}/`, { auth: true })
}

export const fetchUserProfile = () => {
  return request('/api/user/profile/', { auth: true })
}

export const fetchCurrentPlan = () => {
  return request('/api/plan/current/', { auth: true })
}

export const updateUserProfile = (payload) => {
  return request('/api/user/profile/', {
    method: 'PUT',
    auth: true,
    body: payload
  })
}
