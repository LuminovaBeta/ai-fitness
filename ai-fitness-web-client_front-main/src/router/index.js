import { createRouter, createWebHistory } from 'vue-router'
import LoginScreen from '../components/LoginScreen.vue'
import Home from '../views/Home.vue'
import Activity from '../views/Activity.vue'
import Profile from '../views/Profile.vue'
import FreeTraining from '../views/FreeTraining.vue'
import TrainingSession from '../views/TrainingSession.vue'
import MyPlan from '../views/MyPlan.vue'

const routes = [
  { path: '/', name: 'Login', component: LoginScreen },
  { path: '/home', name: 'Home', component: Home },
  { path: '/activity', name: 'Activity', component: Activity },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/my-plan', name: 'MyPlan', component: MyPlan },
  { path: '/free-training', name: 'FreeTraining', component: FreeTraining },
  { path: '/training-session', name: 'TrainingSession', component: TrainingSession }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('auth_token')
  const isPublicRoute = to.path === '/'

  if (!token && !isPublicRoute) {
    sessionStorage.removeItem('welcome_voice_pending')
    sessionStorage.removeItem('login_context')
    sessionStorage.removeItem('plan_ready_toast')
    return '/'
  }

  if (token && isPublicRoute) {
    return '/home'
  }

  return true
})

export default router