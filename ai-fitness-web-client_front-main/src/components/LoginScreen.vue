<template>
  <div class="relative w-full h-full flex items-center justify-center overflow-hidden">
    
    <div 
      class="flex flex-col items-center transition-all duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
      :class="isPasswordMode ? '-translate-x-[280px] scale-80' : 'translate-x-0 scale-100'"
    >
      
      <div class="relative flex items-center justify-center w-[340px] h-[340px]">
        <div class="absolute inset-0 rounded-full bg-gradient-to-tr from-ai-start via-neon-green to-ai-end animate-spin-slow shadow-[0_0_40px_rgba(50,255,126,0.3)]"></div>
        
        <div class="absolute inset-[4px] bg-black rounded-full overflow-hidden flex items-center justify-center z-10">
          
          <video 
            ref="videoRef" 
            class="absolute inset-0 w-full h-full object-cover transform -scale-x-100" 
            autoplay 
            playsinline 
            muted
          ></video>

          <div v-show="!isPasswordMode" class="absolute inset-0 flex items-center justify-center z-20 bg-black/30 pointer-events-none">
            <ScanFace class="w-36 h-36 text-neon-green opacity-80 animate-breath drop-shadow-[0_0_20px_rgba(50,255,126,0.8)]" stroke-width="1.2" />
          </div>

          <div v-show="!isPasswordMode" class="absolute top-0 w-full h-2 bg-neon-green shadow-[0_0_20px_#32FF7E] z-30 animate-scan pointer-events-none"></div>
        </div>
      </div>

      <div class="mt-12 text-center transition-all duration-500" :class="isPasswordMode ? 'opacity-0' : 'opacity-100'">
        <h2 class="text-4xl font-bold tracking-widest drop-shadow-md" :class="scanStatus.color">{{ scanStatus.title }}</h2>
        <p class="text-xl text-gray-400 mt-4 font-medium">{{ scanStatus.desc }}</p>
      </div>

      <button 
        @click="switchMode(true)"
        class="mt-10 px-10 py-5 rounded-full glass-panel-light flex items-center gap-3 hover:bg-white/10 active:scale-95 transition-all duration-300 z-50 shadow-xl"
        :class="isPasswordMode ? 'opacity-0 pointer-events-none' : 'opacity-100'"
      >
        <User class="w-6 h-6 text-gray-300" />
        <span class="text-xl font-bold tracking-wider">账号密码登录</span>
      </button>
    </div>

    <canvas ref="canvasRef" class="hidden"></canvas>

    <!-- 注册弹窗 -->
    <div v-if="isRegisterOpen" class="fixed inset-0 z-60 flex items-center justify-center bg-black/70 backdrop-blur-md p-6" @click.self="closeRegister">
      <div class="w-[760px] max-w-[95vw] max-h-[90vh] overflow-auto rounded-[2rem] p-8 glass-panel-light border border-white/15 shadow-[0_30px_80px_rgba(0,0,0,.55)]">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <p class="text-xs tracking-[0.32em] text-neon-green/90 uppercase">AI Fitness Onboarding</p>
            <h3 class="text-3xl font-bold mt-2">创建新账号</h3>
            <p class="text-gray-400 mt-2">共 3 步，约 30 秒完成初始化</p>
          </div>
          <button @click="closeRegister" class="w-11 h-11 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-xl">✕</button>
        </div>

        <div class="mb-7">
          <div class="flex items-center gap-3">
            <template v-for="step in regSteps" :key="step.id">
              <div class="flex items-center gap-3 flex-1">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border transition-all"
                  :class="step.id <= regStep ? 'bg-neon-green text-black border-neon-green shadow-[0_0_18px_rgba(50,255,126,.45)]' : 'bg-white/5 text-gray-400 border-white/20'">
                  {{ step.id }}
                </div>
                <div class="text-sm" :class="step.id <= regStep ? 'text-white' : 'text-gray-500'">{{ step.title }}</div>
              </div>
            </template>
          </div>
          <div class="h-1.5 mt-4 rounded-full bg-white/10 overflow-hidden">
            <div class="h-full bg-gradient-to-r from-neon-green to-ai-end transition-all duration-500" :style="{ width: `${(regStep / 3) * 100}%` }"></div>
          </div>
        </div>

        <div class="space-y-4">
          <div v-if="regStep === 1" class="space-y-4">
            <p class="text-sm text-gray-400">步骤 1 / 3 · 创建账号</p>

            <div>
              <label class="block text-sm text-gray-300 mb-2">用户名</label>
              <input v-model.trim="registerForm.username" placeholder="请输入用户名" class="w-full h-13 rounded-xl px-4 bg-white/5 border border-white/10 focus:border-neon-green/80 focus:bg-white/10 outline-none transition-all" />
            </div>

            <div>
              <label class="block text-sm text-gray-300 mb-2">密码</label>
              <input v-model="registerForm.password" type="password" placeholder="请输入密码（建议 6 位以上）" class="w-full h-13 rounded-xl px-4 bg-white/5 border border-white/10 focus:border-neon-green/80 focus:bg-white/10 outline-none transition-all" />
            </div>

            <p class="text-xs text-gray-500">账号用于密码登录，人脸功能可在登录后补充录入。</p>

            <div class="flex justify-end gap-3 pt-2">
              <button @click="closeRegister" class="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all">取消</button>
              <button @click="nextRegStep" :disabled="!canStep1" class="px-7 py-2.5 rounded-xl font-semibold transition-all"
                :class="canStep1 ? 'btn-neon-primary' : 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/10'">
                下一步
              </button>
            </div>
          </div>

          <div v-else-if="regStep === 2" class="space-y-4">
            <p class="text-sm text-gray-400">步骤 2 / 3 · 个人信息</p>

            <div>
              <label class="block text-sm text-gray-300 mb-2">性别</label>
              <div class="grid grid-cols-2 gap-3">
                <button type="button" @click="registerForm.gender='M'" :aria-pressed="registerForm.gender==='M'"
                  :class="registerForm.gender==='M' ? 'bg-neon-green text-black border-neon-green' : 'bg-white/5 text-white border-white/10 hover:bg-white/10'"
                  class="h-12 rounded-xl border text-base font-medium transition-all">男</button>
                <button type="button" @click="registerForm.gender='F'" :aria-pressed="registerForm.gender==='F'"
                  :class="registerForm.gender==='F' ? 'bg-neon-green text-black border-neon-green' : 'bg-white/5 text-white border-white/10 hover:bg-white/10'"
                  class="h-12 rounded-xl border text-base font-medium transition-all">女</button>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm text-gray-300 mb-2">身高（cm）</label>
                <input v-model.number="registerForm.height" type="number" min="80" max="260" placeholder="例如 170" class="w-full h-12 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/80 outline-none transition-all" />
              </div>
              <div>
                <label class="block text-sm text-gray-300 mb-2">体重（kg）</label>
                <input v-model.number="registerForm.weight" type="number" min="20" max="300" placeholder="例如 65" class="w-full h-12 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/80 outline-none transition-all" />
              </div>
            </div>

            <div>
              <label class="block text-sm text-gray-300 mb-2">出生日期（可选）</label>
              <div class="rounded-xl border border-white/10 bg-white/5 p-2">
                <div class="relative">
                  <input ref="birthInput" v-model="registerForm.birthdate" type="date" :max="today" class="w-full h-12 rounded-lg px-3 pr-14 bg-black/20 border border-white/10 focus:border-neon-green/80 outline-none transition-all text-white" />
                  <button type="button" @click="focusBirth" class="absolute right-1.5 top-1/2 -translate-y-1/2 w-10 h-10 rounded-lg bg-white/8 border border-white/15 text-white hover:bg-white/12 flex items-center justify-center transition-all">
                    <Calendar class="w-5 h-5" />
                  </button>
                </div>
                <div class="grid grid-cols-3 gap-2 mt-2">
                  <button type="button" @click="setBirthByAge(18)" class="h-9 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-200 hover:bg-white/10 transition-all">18岁</button>
                  <button type="button" @click="setBirthByAge(25)" class="h-9 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-200 hover:bg-white/10 transition-all">25岁</button>
                  <button type="button" @click="setBirthByAge(30)" class="h-9 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-200 hover:bg-white/10 transition-all">30岁</button>
                </div>
              </div>
            </div>

            <div class="flex justify-between gap-3 pt-2">
              <button @click="prevRegStep" class="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all">上一步</button>
              <button @click="nextRegStep" :disabled="!canStep2" class="px-7 py-2.5 rounded-xl font-semibold transition-all"
                :class="canStep2 ? 'btn-neon-primary' : 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/10'">
                下一步
              </button>
            </div>
          </div>

          <div v-else-if="regStep === 3" class="space-y-4">
            <p class="text-sm text-gray-400">步骤 3 / 3 · 目标与确认</p>

            <div>
              <label class="block text-sm text-gray-300 mb-2">健身目标（单选）</label>
              <div class="grid grid-cols-2 gap-3">
                <button
                  v-for="goal in goalOptions"
                  :key="goal"
                  type="button"
                  @click="registerForm.goal = goal"
                  :aria-pressed="registerForm.goal === goal"
                  class="h-12 rounded-xl border px-3 text-sm font-medium transition-all text-left"
                  :class="registerForm.goal === goal ? 'bg-neon-green text-black border-neon-green shadow-[0_0_18px_rgba(50,255,126,.35)]' : 'bg-white/5 text-white border-white/10 hover:bg-white/10'"
                >
                  {{ goal }}
                </button>
              </div>
              <input v-if="registerForm.goal==='其他'" v-model.trim="registerForm.customGoal" placeholder="请输入自定义目标" class="w-full h-12 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/80 outline-none mt-3 text-white" />
            </div>

            <div class="mt-4 p-4 bg-black/25 rounded-xl border border-white/10">
              <p class="text-sm text-gray-300 mb-3">请确认以下信息</p>
              <div class="grid grid-cols-2 gap-y-2 text-sm">
                <p class="text-gray-400">用户名</p><p class="text-white">{{ registerForm.username }}</p>
                <p class="text-gray-400">性别</p><p class="text-white">{{ registerForm.gender === 'M' ? '男' : '女' }}</p>
                <p class="text-gray-400">出生日期</p><p class="text-white">{{ registerForm.birthdate || '--' }}</p>
                <p class="text-gray-400">身高 / 体重</p><p class="text-white">{{ registerForm.height }} cm / {{ registerForm.weight }} kg</p>
                <p class="text-gray-400">目标</p><p class="text-white">{{ finalGoal }}</p>
              </div>
            </div>

            <p v-if="registerError" class="text-neon-red mt-2">{{ registerError }}</p>
            <div class="flex justify-between gap-3 pt-2">
              <button @click="prevRegStep" class="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all">上一步</button>
              <button @click="handleRegister" :disabled="submitRegisterDisabled" class="px-7 py-2.5 rounded-xl font-semibold transition-all"
                :class="submitRegisterDisabled ? 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/10' : 'btn-neon-primary'">
                <span v-if="registerLoading">创建中...</span>
                <span v-else>创建并登录</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>


    <div 
      class="absolute right-24 w-[560px] max-w-[42vw] glass-panel-light border border-white/15 p-10 rounded-[2rem] flex flex-col transition-all duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)] z-50 shadow-[0_30px_80px_rgba(0,0,0,.5)]"
      :class="isPasswordMode ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-32 pointer-events-none'"
    >
      <div class="flex items-start justify-between mb-8 gap-4">
        <div>
          <p class="text-xs tracking-[0.32em] text-neon-green/90 uppercase">AI Fitness Access</p>
          <h3 class="text-3xl font-bold mt-2 text-white">账号登录</h3>
          <p class="text-gray-400 mt-2">使用账号密码进入训练空间</p>
        </div>
        <button @click="switchMode(false)" class="w-11 h-11 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-gray-300 flex items-center justify-center">
          <ArrowLeft class="w-8 h-8" />
        </button>
      </div>
      
      <form @submit.prevent="handleAccountLogin" class="space-y-6">
        <div class="space-y-2">
          <label class="block text-sm text-gray-300">用户名</label>
          <div class="relative flex items-center">
            <User class="w-5 h-5 text-gray-400 absolute left-4" />
            <input 
              v-model="loginForm.username" 
              type="text" 
              placeholder="请输入用户名"
              class="w-full h-12 bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 text-base text-white outline-none focus:border-neon-green/80 focus:bg-white/10 transition-all"
            >
          </div>
        </div>

        <div class="space-y-2">
          <label class="block text-sm text-gray-300">密码</label>
          <div class="relative flex items-center">
            <Lock class="w-5 h-5 text-gray-400 absolute left-4" />
            <input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="请输入密码"
              class="w-full h-12 bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 text-base text-white outline-none focus:border-neon-green/80 focus:bg-white/10 transition-all"
            >
          </div>
        </div>

        <p v-if="errorMessage" class="text-neon-red text-sm h-5">{{ errorMessage }}</p>

        <button 
          type="submit"
          :disabled="isLoading"
          class="w-full mt-2 py-3 rounded-xl text-base font-semibold transition-all duration-300 flex justify-center items-center gap-2"
          :class="(loginForm.username && loginForm.password) ? 'btn-neon-primary' : 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/10'"
        >
          <Loader2 v-if="isLoading" class="w-5 h-5 animate-spin" />
          {{ isLoading ? '登录中...' : '进入系统' }}
        </button>
        <div class="pt-1 flex justify-between items-center text-sm">
          <button type="button" @click="openRegister" class="text-gray-300 hover:text-white transition-all">没有账号？去注册</button>
          <a href="#" class="text-gray-400 hover:text-white transition-all">忘记密码</a>
        </div>
      </form>
    </div>

  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { User, Lock, ArrowLeft, Loader2, ScanFace, Calendar } from '@lucide/vue'
import { loginByAccount, loginByFace, registerAccount } from '../api/auth'
import { initGeneratePlan } from '../api/train'
const router = useRouter()

const isPasswordMode = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const videoRef = ref(null)
const canvasRef = ref(null)
let stream = null
let scanInterval = null
const PREFERRED_CAMERA_NAME = 'Global Shutter Camera'

const scanStatus = reactive({
  title: '靠近即可唤醒',
  desc: '请面向屏幕，系统正在识别身份...',
  color: 'text-white'
})

const PLAN_READY_TOAST_KEY = 'plan_ready_toast'

const getGreetingByTime = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 8) return '早上好'
  if (hour >= 8 && hour < 12) return '上午好'
  if (hour >= 12 && hour < 14) return '中午好'
  if (hour >= 14 && hour < 18) return '下午好'
  if (hour >= 18 && hour < 23) return '晚上好'
  return '夜深了'
}

const matchesPreferredCameraLabel = (label) => {
  const text = String(label || '').toLowerCase()
  if (!text) return false
  if (text.includes(PREFERRED_CAMERA_NAME.toLowerCase())) return true
  return /global\s*shutter/.test(text) && /camera/.test(text)
}

const logVideoInputDevices = (devices) => {
  const videoInputs = (devices || [])
    .filter((d) => d.kind === 'videoinput')
    .map((d, index) => ({
      index,
      label: d.label || '(empty label)',
      deviceId: d.deviceId,
      groupId: d.groupId
    }))
  console.log('[Camera] videoinput devices:', videoInputs)
}

const enumerateVideoDevices = async (tag = 'default') => {
  if (!navigator.mediaDevices?.enumerateDevices) {
    console.warn('[Camera] enumerateDevices unavailable')
    return []
  }
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    console.log(`[Camera] enumerate(${tag}) done`)
    logVideoInputDevices(devices)
    return devices
  } catch (e) {
    console.warn(`[Camera] enumerate(${tag}) failed`, e)
    return []
  }
}

const getVideoDevicesWithPermission = async () => {
  let devices = await enumerateVideoDevices('before-permission')
  const hasLabeled = devices.some((d) => d.kind === 'videoinput' && String(d.label || '').trim())
  if (hasLabeled) return devices

  try {
    const probe = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    probe.getTracks().forEach((track) => track.stop())
  } catch (e) {
    console.warn('[Camera] permission probe failed', e)
  }

  devices = await enumerateVideoDevices('after-permission')
  return devices
}

const getPreferredVideoConstraints = async () => {
  const base = { width: 640, height: 480 }
  if (!navigator.mediaDevices) {
    return { preferred: null, fallback: base }
  }

  const devices = await getVideoDevicesWithPermission()
  const preferred = devices.find(
    (d) => d.kind === 'videoinput' && matchesPreferredCameraLabel(d.label)
  )
  if (preferred?.deviceId) {
    return {
      preferred: {
        width: 640,
        height: 480,
        deviceId: { exact: preferred.deviceId }
      },
      fallback: base
    }
  }

  return { preferred: null, fallback: base }
}

const openCameraWithFallback = async () => {
  const { preferred, fallback } = await getPreferredVideoConstraints()

  if (preferred) {
    try {
      return await navigator.mediaDevices.getUserMedia({
        video: preferred,
        audio: false
      })
    } catch (e) {
      console.warn('指定 Global Shutter Camera 失败，回退默认摄像头', e)
    }
  }

  return await navigator.mediaDevices.getUserMedia({
    video: fallback,
    audio: false
  })
}

const startCamera = async () => {
  try {
    stream = await openCameraWithFallback()
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      videoRef.value.onloadedmetadata = () => {
        startFacePolling()
      }
    }
  } catch (err) {
    console.error("摄像头调用失败:", err)
    scanStatus.title = '摄像头未就绪'
    scanStatus.desc = '请检查一体机摄像头硬件连接'
    scanStatus.color = 'text-neon-red'
  }
}

const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
  }
  stopFacePolling()
}

const captureAndSendFace = async () => {
  // 如果处于密码输入模式，或正在处理登录，则停止发送人脸流
  if (isPasswordMode.value || isLoading.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  if (!video || !canvas) return

  const ctx = canvas.getContext('2d')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  
  const base64Image = canvas.toDataURL('image/jpeg', 0.8)

  try {
    const data = await loginByFace(base64Image)
      
    // 核心业务逻辑：通过后端传回的细分 code，改变 UI 的文案和发光颜色
    switch (data.code) {
      case 'AUTH_SUCCESS':
        stopFacePolling()
        scanStatus.title = '识别成功'
        scanStatus.desc = `${getGreetingByTime()}，${data.username}`
        scanStatus.color = 'text-neon-green'  // 绿色：放行
        handleLoginSuccess(data.access)
        break
        
      case 'NO_FACE':
        scanStatus.title = '靠近即可唤醒...'
        scanStatus.desc = data.msg            // "未检测到人脸，请面向屏幕"
        scanStatus.color = 'text-white'       // 白色：常态
        break
        
      case 'TOO_FAR':
      case 'NOT_FACING':
        scanStatus.title = '请调整姿态'
        scanStatus.desc = data.msg            // "请靠近体测一体机摄像头" / "请抬起头，正对屏幕中央"
        scanStatus.color = 'text-neon-orange' // 橙色：警告用户调整
        break
        
      case 'IMG_ERROR':
        scanStatus.title = '图像异常'
        scanStatus.desc = data.msg
        scanStatus.color = 'text-neon-red'    // 红色：错误
        break
        
      default:
        scanStatus.title = '识别中...'
        scanStatus.desc = data.msg || '正在比对人脸特征'
        scanStatus.color = 'text-white'
    }
  } catch (error) {
    if (error.status === 404) {
      scanStatus.title = '未匹配到档案'
      scanStatus.desc = error.data?.msg || '请先使用账号密码登录，并完成人脸录入'
      scanStatus.color = 'text-neon-orange'
    } else if (error.status === 403) {
      scanStatus.title = '账号异常'
      scanStatus.desc = error.data?.msg || '该账号已被禁用'
      scanStatus.color = 'text-neon-red'
    } else {
      scanStatus.title = '暂时无法识别'
      scanStatus.desc = error.data?.msg || '识别暂时不可用，请稍后重试'
      scanStatus.color = 'text-neon-red'
    }
  }
}

const startFacePolling = () => {
  if (!scanInterval) {
    scanInterval = setInterval(captureAndSendFace, 1500)
  }
}

const stopFacePolling = () => {
  if (scanInterval) {
    clearInterval(scanInterval)
    scanInterval = null
  }
}

const switchMode = (isPassword) => {
  isPasswordMode.value = isPassword
  errorMessage.value = ''
  if (isPassword) {
    stopFacePolling()
  } else {
    startFacePolling()
  }
}

// 注册弹窗与逻辑
const isRegisterOpen = ref(false)
const registerLoading = ref(false)
const registerError = ref('')
const registerForm = reactive({
  username: '',
  password: '',
  gender: 'M',
  height: 170,
  weight: 65,
  birthdate: '',
  goal: '减脂塑形',
  customGoal: ''
})
const today = new Date().toISOString().slice(0, 10)
const birthInput = ref(null)
const regSteps = [
  { id: 1, title: '账号' },
  { id: 2, title: '身体信息' },
  { id: 3, title: '目标确认' }
]
const goalOptions = ['减脂塑形', '增肌', '提升耐力', '增强柔韧性', '其他']

const canStep1 = computed(() => {
  return registerForm.username.trim().length >= 2 && registerForm.password.length >= 6
})

const canStep2 = computed(() => {
  const h = Number(registerForm.height)
  const w = Number(registerForm.weight)
  return Number.isFinite(h) && Number.isFinite(w) && h >= 80 && h <= 260 && w >= 20 && w <= 300
})

const finalGoal = computed(() => {
  if (registerForm.goal === '其他') {
    return registerForm.customGoal.trim()
  }
  return registerForm.goal
})

const submitRegisterDisabled = computed(() => {
  return registerLoading.value || !finalGoal.value
})

const focusBirth = () => {
  if (birthInput.value) birthInput.value.showPicker?.() || birthInput.value.focus()
}

const setBirthByAge = (age) => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - age)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  registerForm.birthdate = `${yyyy}-${mm}-${dd}`
}
const regStep = ref(1)

const resetRegisterForm = () => {
  registerForm.username = ''
  registerForm.password = ''
  registerForm.gender = 'M'
  registerForm.height = 170
  registerForm.weight = 65
  registerForm.birthdate = ''
  registerForm.goal = '减脂塑形'
  registerForm.customGoal = ''
}

const nextRegStep = () => {
  if (regStep.value === 1 && !canStep1.value) {
    registerError.value = '请输入至少 2 位用户名和 6 位密码'
    return
  }
  if (regStep.value === 2 && !canStep2.value) {
    registerError.value = '请填写合理的身高与体重范围'
    return
  }
  registerError.value = ''
  if (regStep.value < 3) regStep.value += 1
}

const prevRegStep = () => {
  registerError.value = ''
  if (regStep.value > 1) regStep.value -= 1
}

const openRegister = () => {
  isRegisterOpen.value = true
  regStep.value = 1
  registerError.value = ''
  resetRegisterForm()
  // 停止摄像头与人脸轮询，避免弹窗被视频/扫描逻辑干扰
  stopFacePolling()
  stopCamera()
}

const closeRegister = () => {
  isRegisterOpen.value = false
  registerError.value = ''
  registerLoading.value = false
  // 恢复摄像头轮询（若非密码模式）
  if (!isPasswordMode.value) startCamera()
  if (!isPasswordMode.value) startFacePolling()
}

const handleRegister = async () => {
  if (!canStep1.value || !canStep2.value || !finalGoal.value) {
    registerError.value = '请先完整填写注册信息'
    return
  }
  registerLoading.value = true
  registerError.value = ''
  try {
    const data = await registerAccount({
      username: registerForm.username,
      password: registerForm.password,
      gender: registerForm.gender,
      height: registerForm.height,
      weight: registerForm.weight,
      birthdate: registerForm.birthdate,
      goal: finalGoal.value
    })
    if (data?.access) {
      localStorage.setItem('auth_token', data.access)
    }

    let planInitStarted = false
    try {
      planInitStarted = true
      await initGeneratePlan({ goal: finalGoal.value })
      sessionStorage.setItem(PLAN_READY_TOAST_KEY, '1')
    } catch (e) {
      sessionStorage.removeItem(PLAN_READY_TOAST_KEY)
    }
    closeRegister()
    handleLoginSuccess(data.access, {
      isFirstLogin: true,
      username: registerForm.username,
      refreshHome: true,
      waitingPlanGeneration: planInitStarted
    })
  } catch (err) {
    registerError.value = err.data?.error || err.message || '注册失败'
  } finally {
    registerLoading.value = false
  }
}

const handleAccountLogin = async () => {
  if (!loginForm.username || !loginForm.password) return
  
  isLoading.value = true
  errorMessage.value = ''

  try {
    const data = await loginByAccount({
      username: loginForm.username,
      password: loginForm.password
    })
    handleLoginSuccess(data.access, {
      username: loginForm.username
    })
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查账号、密码或网络状态'
  } finally {
    isLoading.value = false
  }
}

const handleLoginSuccess = (token, options = {}) => {
  if (token) {
    localStorage.setItem('auth_token', token)
    sessionStorage.setItem('welcome_voice_pending', '1')
    sessionStorage.setItem('login_context', JSON.stringify({
      isFirstLogin: !!options.isFirstLogin,
      username: options.username || '',
      loginAt: Date.now(),
      refreshHome: !!options.refreshHome,
      waitingPlanGeneration: !!options.waitingPlanGeneration
    }))
    // 延迟 800ms，让用户看清楚“识别成功”的绿色字样，然后再丝滑切走
    setTimeout(() => {
      router.replace({
        path: '/home',
        query: options.refreshHome ? { refresh: '1' } : undefined
      })
    }, 800)
  }
}

onMounted(() => {
  startCamera()
})

onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped>
/* 避免视频画面水平翻转导致的不适（镜面效果） */
.transform.-scale-x-100 {
  transform: scaleX(-1);
}

/* 独立的外层流光圆环旋转动画，不影响内部视频 */
.animate-spin-slow {
  animation: spin 6s linear infinite;
}

/* 模拟科幻扫描线从上到下移动 */
@keyframes scan {
  0% { transform: translateY(-10px); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(320px); opacity: 0; }
}
.animate-scan {
  animation: scan 2.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

/* 注册向导触屏优化样式 */
.btn-neon-primary {
  background: linear-gradient(90deg, #00FFA3, #32FF7E);
  color: #021;
}

.bg-neon-green { background-color: #32FF7E; }

/* 输入和选择文字颜色保证可见 */
select, input[type="text"], input[type="date"], input[type="number"], textarea {
  color: #fff;
}

.bg-white\/6 { background-color: rgba(255,255,255,0.06); }

/* 确保原生下拉项可见（部分浏览器支持） */
select option {
  color: #000;
  background: #fff;
}

</style>