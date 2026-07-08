import { request } from './http'

export const fetchRosRuntimeConfig = () => {
  return request('/api/runtime/ros-config/', {
    method: 'GET'
  })
}
