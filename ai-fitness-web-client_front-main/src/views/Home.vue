<template>
  <div class="w-full h-full p-8 flex flex-col relative">
    
    <header class="flex justify-between items-end mb-10">
      <div>
        <h2 class="text-5xl font-bold tracking-tight mb-2">{{ greetingText }}, <span class="text-neon-green">{{ dashboardData.user_info.username }}</span></h2>
        <p class="text-xl text-gray-400 font-medium">{{ headerSubtitle }}</p>
      </div>
      <div class="text-right">
        <p class="text-4xl font-mono text-white tracking-widest">{{ currentTime }}</p>
      </div>
    </header>

    <div v-if="planReadyToastVisible" class="mb-4 px-7 py-4 rounded-2xl border border-neon-green/30 bg-neon-green/12 text-neon-green shadow-[0_0_24px_rgba(50,255,126,0.18)] animate-fade-in-up">
      <div class="flex items-center gap-3">
        <span class="text-2xl">✅</span>
        <div>
          <p class="text-xl font-bold">{{ planToastTitle }}</p>
          <p class="text-sm text-neon-green/80 mt-1">{{ planToastDesc }}</p>
        </div>
      </div>
    </div>

    <div v-if="statusMessage.text" class="mb-4 px-6 py-3 rounded-lg" :class="statusMessage.type === 'error' ? 'bg-neon-red/10 text-neon-red' : (statusMessage.type === 'warning' ? 'bg-neon-orange/10 text-neon-orange' : 'bg-neon-green/10 text-neon-green')">
      {{ statusMessage.text }}
    </div>

    <div class="flex-1 grid grid-cols-12 gap-8 h-full pb-6">
      
      <div class="col-span-5 glass-panel rounded-[2rem] flex flex-col items-center justify-center relative shadow-2xl p-6 overflow-hidden">
        <h3 class="absolute top-8 left-8 text-2xl font-bold tracking-widest text-gray-300">今日完成度</h3>
        
        <div class="relative w-72 h-72 flex items-center justify-center mt-4">
          <svg viewBox="0 0 100 100" class="w-full h-full transform -rotate-90 drop-shadow-[0_0_20px_rgba(50,255,126,0.3)]">
            <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.05)" stroke-width="8" fill="none" />
            <circle 
              cx="50" cy="50" r="42" 
              stroke="#32FF7E" stroke-width="8" fill="none" 
              stroke-dasharray="264" 
              :stroke-dashoffset="264 - (264 * dashboardData.plan_status.progress_percent / 100)" 
              stroke-linecap="round" 
              class="transition-all duration-[2000ms] ease-out" 
            />
          </svg>
          <div class="absolute flex flex-col items-center justify-center text-center">
            <span class="text-7xl font-black tracking-tighter text-white">{{ dashboardData.plan_status.progress_percent }}<span class="text-3xl">%</span></span>
            <span class="text-gray-400 font-medium mt-1 tracking-widest">PROGRESS</span>
          </div>
        </div>

        <div class="absolute bottom-10 w-full px-10 flex justify-between text-center items-center">
          <div>
            <p class="text-gray-400 text-sm tracking-wider mb-2">近7日耗时</p>
            <p class="text-2xl font-bold text-white"><span class="text-neon-orange mr-1 text-3xl">{{ dashboardData.weekly_duration_mins }}</span>MIN</p>
          </div>
          <div class="w-[2px] h-12 bg-white/10 rounded-full"></div>
          <div>
            <p class="text-gray-400 text-sm tracking-wider mb-2">身体指数 BMI</p>
            <p class="text-2xl font-bold text-white" :class="bmiStatusColor">{{ bmiValue }}</p>
          </div>
        </div>
      </div>

      <div class="col-span-7 flex flex-col gap-6">
        
        <div class="flex-1 glass-panel rounded-[2rem] p-8 flex flex-col shadow-xl">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-2xl font-bold tracking-widest flex items-center gap-3">
              <span class="w-3 h-8 bg-neon-green rounded-full shadow-[0_0_10px_#32FF7E]"></span>
              今日 AI 专属计划
            </h3>
            <span v-if="dashboardData.plan_status.is_completed && dashboardData.plan_status.today_exercises.length > 0" class="px-5 py-2 rounded-full bg-neon-green/20 text-neon-green text-sm font-bold border border-neon-green/30">
              ✅ 全目标达成
            </span>
          </div>
          
          <div class="flex-1 overflow-y-auto space-y-4 pr-2">
            <template v-if="dashboardData.plan_status.today_exercises.length > 0">
              <div v-for="(exercise, index) in dashboardData.plan_status.today_exercises" :key="index" 
                   class="flex items-center justify-between p-5 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                <div class="flex items-center gap-5">
                  <div class="w-14 h-14 rounded-full bg-black/40 flex items-center justify-center border border-white/10 text-2xl">
                    {{ getExerciseIcon(exercise.type) }}
                  </div>
                  <div>
                    <p class="text-2xl font-bold tracking-wider">{{ getExerciseName(exercise) }}</p>
                    <p class="text-gray-400 mt-1">单组建议: {{ (exercise.target / (exercise.sets || 1)).toFixed(0) || exercise.target }} 次 / 共 {{ exercise.sets || 1 }} 组</p>
                  </div>
                </div>
                <div class="text-right">
                  <p class="text-3xl font-mono font-bold" :class="exercise.is_done ? 'text-neon-green' : 'text-white'">
                    {{ exercise.actual }} <span class="text-lg text-gray-500">/ {{ exercise.target }}</span>
                  </p>
                </div>
              </div>
            </template>
            
            <div v-else class="h-full flex flex-col items-center justify-center text-gray-400 opacity-80">
              <span class="text-6xl mb-4">☕️</span>
              <p class="text-2xl font-bold tracking-widest">今日为修复日</p>
              <p class="text-lg mt-2">肌肉正在重组，好好休息一天吧</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-6 h-32">
          <button 
            @click="startTodayPlan"
            :disabled="isStartingPlan || dashboardData.plan_status.is_completed || dashboardData.plan_status.today_exercises.length === 0"
            class="rounded-[2rem] flex flex-col items-center justify-center group transition-all"
            :class="(dashboardData.plan_status.is_completed || dashboardData.plan_status.today_exercises.length === 0) ? 'bg-white/5 border border-white/10 text-gray-500' : 'btn-neon-primary shadow-[0_0_20px_rgba(50,255,126,0.3)]'"
          >
            <span class="text-2xl font-black tracking-widest group-active:scale-95 transition-transform">启动今日计划</span>
            <span class="text-sm font-bold mt-2 tracking-wider group-active:scale-95 transition-transform" :class="(dashboardData.plan_status.is_completed || dashboardData.plan_status.today_exercises.length === 0) ? 'text-gray-600' : 'text-black/60'">AI 指导 & 动作矫正</span>
          </button>
          
          <button
            @click="router.push('/free-training')"
            class="bg-white/10 hover:bg-white/20 active:bg-white/5 border border-white/20 rounded-[2rem] flex flex-col items-center justify-center transition-all group shadow-lg"
          >
            <span class="text-2xl font-bold tracking-widest text-white group-active:scale-95 transition-transform">自由训练</span>
            <span class="text-sm text-gray-400 font-medium mt-2 tracking-wider group-active:scale-95 transition-transform">自选动作，随心记录</span>
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDashboard } from '../api/user'
import { fetchExercises, startTrainSession } from '../api/train'
const speakWithBackendTts = inject('speakWithBackendTts')

const router = useRouter()
const WELCOME_VOICE_PENDING_KEY = 'welcome_voice_pending'
const PLAN_READY_TOAST_KEY = 'plan_ready_toast'
const DASHBOARD_POLL_INTERVAL_MS = 6000
let planReadyToastTimer = null
let planPollTimer = null
let dashboardRefreshInterval = null
let isPollingPlan = false

// --- 时钟逻辑 ---
const currentTime = ref('')
let timeInterval = null

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// --- 数据模型 ---
const dashboardData = reactive({
  user_info: { username: '用户', gender: '', height: 170, weight: 65 },
  weekly_duration_mins: 0,
  plan_status: {
    active_plan_id: null,
    is_completed: false,
    progress_percent: 0,
    today_exercises: []
  }
})

const isStartingPlan = ref(false)
const statusMessage = reactive({ type: 'ok', text: '' })
const planReadyToastVisible = ref(false)
const planToastTitle = ref('你的训练计划已生成完成')
const planToastDesc = ref('可以直接开始今天的训练，或先查看完整安排。')
const hasActivePlan = computed(() => !!dashboardData.plan_status?.active_plan_id)
const isWaitingPlanGeneration = computed(() => !!loginContext.value?.waitingPlanGeneration)

const getGreetingByTime = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 8) return '早上好'
  if (hour >= 8 && hour < 12) return '上午好'
  if (hour >= 12 && hour < 14) return '中午好'
  if (hour >= 14 && hour < 18) return '下午好'
  if (hour >= 18 && hour < 23) return '晚上好'
  return '夜深了'
}

const greetingText = computed(() => getGreetingByTime())

const loginContext = computed(() => {
  try {
    const raw = sessionStorage.getItem('login_context')
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
})

const headerSubtitle = computed(() => {
  if (loginContext.value?.isFirstLogin && loginContext.value?.waitingPlanGeneration) {
    return '欢迎加入，专属训练计划已为你准备中。'
  }
  if (loginContext.value?.isFirstLogin) {
    return '欢迎加入，专属训练计划已经准备好了。'
  }
  if (dashboardData.plan_status.today_exercises.length === 0) {
    return '今天安排以恢复放松为主，记得给身体一点缓冲时间。'
  }
  if (dashboardData.plan_status.is_completed) {
    return '今天的训练已经完成，继续保持这个节奏。'
  }
  return '今天有一组训练计划等待完成，准备好开始了吗？'
})

const showPlanToast = (title, desc) => {
  planToastTitle.value = title
  planToastDesc.value = desc
  planReadyToastVisible.value = true
  if (planReadyToastTimer) clearTimeout(planReadyToastTimer)
  planReadyToastTimer = setTimeout(() => {
    planReadyToastVisible.value = false
    planReadyToastTimer = null
  }, 4500)
}

const showPlanReadyToast = () => {
  showPlanToast('你的训练计划已生成完成', '可以直接开始今天的训练，或先查看完整安排。')
}

const showPlanUpdatedToast = () => {
  showPlanToast('训练计划已更新', '已根据你最新训练表现优化后续安排。')
}

const clearPlanPolling = () => {
  if (planPollTimer) {
    clearTimeout(planPollTimer)
    planPollTimer = null
  }
}

const stopPlanWaitingState = () => {
  const nextContext = {
    ...loginContext.value,
    waitingPlanGeneration: false
  }
  sessionStorage.setItem('login_context', JSON.stringify(nextContext))
  clearPlanPolling()
}

const schedulePlanPolling = (delay = 4000) => {
  clearPlanPolling()
  planPollTimer = setTimeout(() => {
    pollPlanGenerationStatus()
  }, delay)
}

// --- 动态计算 BMI ---
const bmiValue = computed(() => {
  const heightM = dashboardData.user_info.height / 100
  const weight = dashboardData.user_info.weight
  if (heightM > 0) {
    const bmi = weight / (heightM * heightM)
    return bmi.toFixed(1)
  }
  return '22.0'
})

const bmiStatusColor = computed(() => {
  const bmi = parseFloat(bmiValue.value)
  if (bmi < 18.5) return 'text-neon-orange' // 偏瘦
  if (bmi >= 18.5 && bmi < 24) return 'text-neon-green' // 正常
  return 'text-neon-red' // 偏胖
})

// --- 动作字典翻译（从配置API读取，避免硬编码） ---
const exerciseDict = ref({})
const exerciseIconFallback = {
  squat: '🦵',
  pushup: '💪',
  push_up: '💪',
  pull_up: '🦍',
  plank: '🧱',
  jumping_jack: '🏃'
}
const getExerciseName = (exercise) => {
  const type = String(exercise?.type || '').trim()
  const serverName = String(exercise?.name || '').trim()
  if (serverName) return serverName
  return exerciseDict.value[type]?.name || type
}
const getExerciseIcon = (type) => exerciseIconFallback[type] || '🔥'

const hydrateExerciseDict = async () => {
  try {
    const data = await fetchExercises()
    const dict = {}
    const list = Array.isArray(data?.exercises) ? data.exercises : []
    for (const item of list) {
      const code = String(item?.code || '').trim()
      if (!code) continue
      dict[code] = {
        name: item?.name_zh || item?.name || code
      }
    }
    exerciseDict.value = dict
  } catch (err) {
    console.warn('读取动作字典失败，使用类型原文显示', err)
    exerciseDict.value = {}
  }
}

// --- 核心方法：拉取数据 ---
const fetchDashboardData = async () => {
  try {
    const data = await fetchDashboard()
    const previousPlanId = dashboardData.plan_status?.active_plan_id
    const hadPlanBefore = !!previousPlanId
    Object.assign(dashboardData, data) // 更新界面

    const currentPlanId = data?.plan_status?.active_plan_id
    const hasPlanNow = !!currentPlanId
    if (isWaitingPlanGeneration.value && hasPlanNow) {
      if (!hadPlanBefore) {
        showPlanReadyToast()
      }
      stopPlanWaitingState()
      statusMessage.text = ''
    } else if (previousPlanId && currentPlanId && previousPlanId !== currentPlanId) {
      showPlanUpdatedToast()
    }

    const username = data?.user_info?.username || '用户'
    const shouldPlayWelcome = sessionStorage.getItem(WELCOME_VOICE_PENDING_KEY) === '1'
    if (shouldPlayWelcome) {
      await triggerWelcomeVoice(username, data.plan_status)
      sessionStorage.removeItem(WELCOME_VOICE_PENDING_KEY)
    }

    if (sessionStorage.getItem(PLAN_READY_TOAST_KEY) === '1') {
      showPlanReadyToast()
      sessionStorage.removeItem(PLAN_READY_TOAST_KEY)
    }
  } catch (err) {
    console.error('主页拉取数据失败:', err)
    if (err.status === 401) {
      localStorage.removeItem('auth_token')
      router.push('/')
    }
  }
}

const startDashboardAutoRefresh = () => {
  if (dashboardRefreshInterval) clearInterval(dashboardRefreshInterval)
  dashboardRefreshInterval = setInterval(() => {
    fetchDashboardData()
  }, DASHBOARD_POLL_INTERVAL_MS)
}

const pollPlanGenerationStatus = async () => {
  if (isPollingPlan || !isWaitingPlanGeneration.value) return
  isPollingPlan = true
  try {
    await fetchDashboardData()
    if (isWaitingPlanGeneration.value && !hasActivePlan.value) {
      schedulePlanPolling(4000)
    }
  } finally {
    isPollingPlan = false
  }
}

const startTodayPlan = async () => {
  if (isStartingPlan.value) return
  if (!dashboardData.plan_status || !dashboardData.plan_status.today_exercises || dashboardData.plan_status.today_exercises.length === 0) return
  isStartingPlan.value = true
  try {
    const exercises = dashboardData.plan_status.today_exercises.map(e => e.type)
    // pick reasonable defaults from first exercise
    const first = dashboardData.plan_status.today_exercises[0] || {}
    const sets = first.sets || 1
    const reps = first.reps_per_set || Math.max(1, Math.floor((first.target || 0) / (sets || 1)))
    const restSec = Math.max(10, Number(first.rest_sec) || 45)

    const payload = {
      mode: 'guided',
      exercises,
      sets,
      reps,
      restSec,
      intensity: 'medium'
    }

    const data = await startTrainSession(payload)
    const sessionId = data.session_id || data.id || ''
    if (sessionId) {
      statusMessage.type = 'ok'
      statusMessage.text = '训练已准备完成，正在进入...'
      router.push({
        path: '/training-session',
        query: {
          sessionId,
          sets: String(sets),
          reps: String(reps),
          restSec: String(restSec),
          exercise: exercises[0] || '',
          exercises: exercises.join(',')
        }
      })
    } else {
      statusMessage.type = 'warning'
      statusMessage.text = '未能同步训练记录，已为你切换到训练页'
      router.push('/training-session')
    }
  } catch (err) {
    console.error('启动今日计划失败', err)
    statusMessage.type = 'error'
    statusMessage.text = '启动计划失败，请稍后再试'
  } finally {
    isStartingPlan.value = false
  }
}

// --- 核心方法：由前端统一触发后端 TTS，并同步气泡动效 ---
const triggerWelcomeVoice = async (username, planStatus) => {
  let textToSpeak = ''
  if (planStatus.today_exercises.length === 0) {
    textToSpeak = `${loginContext.value?.isFirstLogin ? '欢迎加入' : getGreetingByTime()}，${username}。今天是恢复日，记得舒展身体，保持轻松节奏。`
  } else if (planStatus.is_completed) {
    textToSpeak = `干得漂亮，${username}！你已经完成了今天所有的训练任务，真是自律的一天。`
  } else {
    textToSpeak = loginContext.value?.isFirstLogin
      ? `欢迎加入，${username}。你的专属训练计划已经准备好了，随时可以开始今天的第一组训练。`
      : `${getGreetingByTime()}，${username}。今天还有 ${100 - planStatus.progress_percent}% 的进度待完成，准备好就开始吧。`
  }
  
  try {
    if (speakWithBackendTts) {
      await speakWithBackendTts(textToSpeak)
    }
  } catch (err) {
    console.error('触发入场语音失败:', err)
  }
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  hydrateExerciseDict()
  fetchDashboardData() // 进入页面即拉取
  startDashboardAutoRefresh()
  if (isWaitingPlanGeneration.value) {
    statusMessage.type = 'ok'
    statusMessage.text = '正在为你生成专属训练计划，请稍候...'
    schedulePlanPolling(4000)
  }
})

onBeforeUnmount(() => {
  if (timeInterval) clearInterval(timeInterval)
  if (dashboardRefreshInterval) clearInterval(dashboardRefreshInterval)
  if (planReadyToastTimer) clearTimeout(planReadyToastTimer)
  clearPlanPolling()
})
</script>

<style scoped>
.animate-fade-in-up {
  animation: fade-in-up .35s ease-out;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>