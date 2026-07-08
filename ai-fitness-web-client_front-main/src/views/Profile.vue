<template>
  <div class="w-full h-full p-8 flex flex-col gap-6 text-white">
    <header class="shrink-0">
      <h2 class="text-4xl font-bold tracking-tight">我的信息</h2>
      <p class="text-gray-400 mt-2">查看账号资料、设备状态与人脸录入情况</p>
    </header>

    <section class="grid grid-cols-12 gap-6 flex-1 min-h-0">
      <div class="col-span-5 glass-panel rounded-[2rem] p-6 flex flex-col gap-4">
        <h3 class="text-2xl font-bold tracking-wider">账号资料</h3>
        <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
          <p class="text-sm text-gray-400">用户名</p>
          <p class="text-xl font-semibold mt-1">{{ displayText(profile.username) }}</p>
        </div>
        <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
          <p class="text-sm text-gray-400">手机号</p>
          <p class="text-xl font-semibold mt-1">{{ displayText(profile.phone) }}</p>
        </div>
        <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
          <p class="text-sm text-gray-400">角色</p>
          <p class="text-xl font-semibold mt-1">{{ displayText(profile.role) }}</p>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
            <p class="text-xs text-gray-400">性别</p>
            <p class="text-lg font-semibold mt-1">{{ displayText(profile.gender) }}</p>
          </div>
          <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
            <p class="text-xs text-gray-400">身高</p>
            <p class="text-lg font-semibold mt-1">{{ displayNumber(profile.height, 'cm') }}</p>
          </div>
          <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
            <p class="text-xs text-gray-400">体重</p>
            <p class="text-lg font-semibold mt-1">{{ displayNumber(profile.weight, 'kg') }}</p>
          </div>
        </div>

        <div class="bg-black/20 rounded-2xl border border-white/10 p-4 flex items-center gap-4">
          <div class="w-14 h-14 rounded-full bg-white/10 border border-white/10 overflow-hidden flex items-center justify-center text-xs text-gray-400">
            <img v-if="profile.avatar" :src="profile.avatar" alt="avatar" class="w-full h-full object-cover" />
            <span v-else>--</span>
          </div>
          <div>
            <p class="text-sm text-gray-400">头像</p>
            <p class="text-sm text-gray-300 mt-1">{{ profile.avatar ? '已配置' : '--' }}</p>
          </div>
        </div>

        <div class="bg-black/20 rounded-2xl border border-white/10 p-4">
          <p class="text-sm text-gray-400">状态</p>
          <p class="text-base mt-1" :class="statusClass">
            {{ statusMessage.text }}
          </p>
        </div>
      </div>

      <div class="col-span-7 glass-panel-light rounded-[2rem] p-6 flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <h3 class="text-2xl font-bold tracking-wider">安全与设备</h3>
          <button
            @click="openSettingsDialog"
            class="h-11 px-5 rounded-xl border border-neon-green/40 bg-neon-green/15 text-neon-green font-semibold hover:bg-neon-green/25 transition-all"
          >
            用户设置
          </button>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <button @click="goMyPlan" class="h-28 rounded-2xl bg-neon-green/15 border border-neon-green/30 hover:bg-neon-green/25 transition-all text-left px-5">
            <p class="text-lg font-bold text-neon-green">我的计划</p>
            <p class="text-sm text-gray-300 mt-2">查看当前 7 天计划并重新生成</p>
          </button>

          <button @click="refreshProfile" :disabled="isLoadingProfile" class="h-28 rounded-2xl bg-white/10 border border-white/15 hover:bg-white/15 transition-all text-left px-5 disabled:opacity-60 disabled:cursor-not-allowed">
            <p class="text-lg font-bold">同步资料</p>
            <p class="text-sm text-gray-400 mt-2">重新刷新当前账号资料</p>
          </button>

          <button @click="toggleFaceEnroll" :class="isFaceBusy ? 'bg-neon-red/20 border-neon-red/40 hover:bg-neon-red/30' : 'bg-white/10 border-white/15 hover:bg-white/15'" class="h-28 rounded-2xl border transition-all text-left px-5">
            <p class="text-lg font-bold">{{ isFaceBusy ? '停止录入' : '人脸录入' }}</p>
            <p class="text-sm text-gray-400 mt-2">{{ isFaceBusy ? '连续采集中，点击可停止' : '连续采集并自动重试' }}</p>
          </button>

          <button @click="checkDevice" class="h-28 rounded-2xl bg-white/10 border border-white/15 hover:bg-white/15 transition-all text-left px-5">
            <p class="text-lg font-bold">设备校准</p>
            <p class="text-sm text-gray-400 mt-2">检查摄像头权限与可用状态</p>
          </button>

          <button @click="logout" class="h-28 rounded-2xl bg-neon-red/20 border border-neon-red/40 hover:bg-neon-red/30 transition-all text-left px-5">
            <p class="text-lg font-bold text-neon-red">退出登录</p>
            <p class="text-sm text-gray-300 mt-2">退出当前账号并返回登录页</p>
          </button>
        </div>

        <div class="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p class="text-sm text-gray-400 mb-3">人脸录入预览</p>
          <div class="grid grid-cols-[220px_1fr] gap-4 items-stretch">
            <div class="relative w-[220px] h-[220px] rounded-2xl border border-white/10 overflow-hidden bg-black/40">
              <video
                ref="faceVideoRef"
                autoplay
                muted
                playsinline
                class="absolute inset-0 w-full h-full object-cover"
              ></video>
              <div v-if="!isFaceBusy" class="absolute inset-0 flex items-center justify-center text-gray-500 text-sm bg-black/40">
                点击“人脸录入”开始连续采集
              </div>
              <div v-else class="absolute inset-0 border-2 border-neon-green/70 animate-pulse"></div>
            </div>
            <div class="rounded-2xl border border-white/10 bg-black/30 p-4 flex flex-col justify-between">
              <div>
                <p class="text-sm text-gray-400">最近一次识别状态</p>
                <p class="text-lg font-semibold mt-2" :class="faceStatusClass">{{ faceFeedback.title }}</p>
                <p class="text-sm text-gray-300 mt-2">{{ faceFeedback.desc }}</p>
              </div>
              <div class="text-xs text-gray-500 mt-4">请保持光线充足并正对镜头</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div
      v-if="isSettingsDialogOpen"
      class="fixed inset-0 z-[70] bg-black/70 backdrop-blur-sm flex items-center justify-center p-6"
      @click.self="closeSettingsDialog"
    >
      <div class="w-[900px] max-w-[92vw] rounded-[2rem] border border-white/15 bg-[#111317]/95 shadow-[0_30px_80px_rgba(0,0,0,.55)] p-6">
        <div class="flex items-start justify-between gap-4 mb-5">
          <div>
            <p class="text-2xl font-bold text-white">用户设置</p>
            <p class="text-sm text-gray-300 mt-1">单独窗口编辑个人信息，避免主界面布局拥挤</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs px-3 py-1 rounded-full border" :class="dirtyTagClass">{{ isDirty ? '未保存' : '已同步' }}</span>
            <button @click="closeSettingsDialog" class="w-10 h-10 rounded-full border border-white/15 bg-white/5 hover:bg-white/10 transition-all">✕</button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-gray-400 mb-1">手机号</label>
            <input
              v-model="settingsForm.phone"
              @input="handlePhoneInput"
              inputmode="numeric"
              type="text"
              maxlength="11"
              placeholder="请输入手机号"
              class="w-full h-11 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/70 outline-none transition-all"
            />
            <p v-if="phoneValidationError" class="text-xs text-neon-red mt-1">{{ phoneValidationError }}</p>
          </div>

          <div>
            <label class="block text-xs text-gray-400 mb-1">性别</label>
            <div class="grid grid-cols-3 gap-2">
              <button type="button" @click="settingsForm.gender = '男'" class="h-11 rounded-xl border text-sm transition-all"
                :class="settingsForm.gender === '男' ? 'bg-neon-green text-black border-neon-green' : 'bg-white/5 text-white border-white/10 hover:bg-white/10'">男</button>
              <button type="button" @click="settingsForm.gender = '女'" class="h-11 rounded-xl border text-sm transition-all"
                :class="settingsForm.gender === '女' ? 'bg-neon-green text-black border-neon-green' : 'bg-white/5 text-white border-white/10 hover:bg-white/10'">女</button>
              <button type="button" @click="settingsForm.gender = ''" class="h-11 rounded-xl border text-sm transition-all"
                :class="settingsForm.gender === '' ? 'bg-neon-green text-black border-neon-green' : 'bg-white/5 text-white border-white/10 hover:bg-white/10'">未设置</button>
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-400 mb-1">身高（cm）</label>
            <input v-model.number="settingsForm.height" type="number" min="80" max="260" placeholder="例如 170" class="w-full h-11 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/70 outline-none transition-all" />
          </div>

          <div>
            <label class="block text-xs text-gray-400 mb-1">体重（kg）</label>
            <input v-model.number="settingsForm.weight" type="number" min="20" max="300" placeholder="例如 65" class="w-full h-11 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/70 outline-none transition-all" />
          </div>

          <div>
            <label class="block text-xs text-gray-400 mb-1">出生日期</label>
            <input v-model="settingsForm.birthdate" type="date" class="w-full h-11 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/70 outline-none transition-all" />
          </div>

          <div>
            <label class="block text-xs text-gray-400 mb-1">头像链接</label>
            <input v-model.trim="settingsForm.avatar" type="text" placeholder="https://..." class="w-full h-11 rounded-xl px-3 bg-white/5 border border-white/10 focus:border-neon-green/70 outline-none transition-all" />
            <p v-if="avatarValidationError" class="text-xs text-neon-red mt-1">{{ avatarValidationError }}</p>
          </div>
        </div>

        <div class="mt-3 rounded-xl border border-white/10 bg-black/25 p-3 flex items-center gap-3">
          <div class="w-14 h-14 rounded-full bg-white/10 border border-white/10 overflow-hidden flex items-center justify-center text-xs text-gray-400 shrink-0">
            <img v-if="avatarPreviewUrl && !avatarPreviewFailed" :src="avatarPreviewUrl" alt="avatar-preview" class="w-full h-full object-cover" @error="avatarPreviewFailed = true" />
            <span v-else>预览</span>
          </div>
          <div class="text-xs text-gray-300 min-w-0">
            <p class="text-gray-400">头像预览</p>
            <p v-if="avatarPreviewUrl && !avatarPreviewFailed" class="truncate mt-1">{{ avatarPreviewUrl }}</p>
            <p v-else-if="avatarPreviewFailed" class="text-neon-orange mt-1">图片加载失败，请检查链接可访问性</p>
            <p v-else class="mt-1">请输入有效的 http/https 图片链接</p>
          </div>
        </div>

        <p v-if="settingsError" class="text-sm text-neon-red mt-3">{{ settingsError }}</p>

        <div class="flex justify-end gap-3 mt-5">
          <button @click="resetSettingsForm" :disabled="isSavingProfile" class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all disabled:opacity-60">重置</button>
          <button @click="saveProfileSettings" :disabled="isSavingProfile || !isDirty" class="px-5 py-2 rounded-xl font-semibold transition-all"
            :class="isSavingProfile || !isDirty ? 'bg-white/5 text-gray-500 border border-white/10 cursor-not-allowed' : 'btn-neon-primary'">
            {{ isSavingProfile ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchUserProfile, updateUserProfile } from '../api/user'
import { registerFace } from '../api/auth'

const router = useRouter()
const speakWithBackendTts = inject('speakWithBackendTts')

const profile = reactive({
  username: '',
  phone: '',
  role: '',
  gender: '',
  height: null,
  weight: null,
  avatar: '',
  birthdate: ''
})

const isLoadingProfile = ref(false)
const isSavingProfile = ref(false)
const isFaceBusy = ref(false)
const isSettingsDialogOpen = ref(false)
const faceVideoRef = ref(null)
const faceLoopActive = ref(false)

const settingsForm = reactive({
  phone: '',
  gender: '',
  height: '',
  weight: '',
  birthdate: '',
  avatar: ''
})

const settingsSnapshot = ref(JSON.stringify({
  phone: '',
  gender: '',
  height: '',
  weight: '',
  birthdate: '',
  avatar: ''
}))
const settingsError = ref('')
const avatarPreviewFailed = ref(false)

let activeMedia = null
let activeTrack = null
const PREFERRED_CAMERA_NAME = 'Global Shutter Camera'

const statusMessage = reactive({
  type: 'ok',
  text: '正在同步资料...'
})

const statusClass = computed(() => {
  if (statusMessage.type === 'error') return 'text-neon-red'
  if (statusMessage.type === 'warning') return 'text-neon-orange'
  return 'text-neon-green'
})

const faceFeedback = reactive({
  type: 'neutral',
  title: '待采集',
  desc: '尚未开始人脸录入'
})

const faceStatusClass = computed(() => {
  if (faceFeedback.type === 'error') return 'text-neon-red'
  if (faceFeedback.type === 'warning') return 'text-neon-orange'
  if (faceFeedback.type === 'success') return 'text-neon-green'
  return 'text-gray-300'
})

const normalizedSettings = computed(() => ({
  phone: settingsForm.phone || '',
  gender: settingsForm.gender || '',
  height: settingsForm.height === '' || settingsForm.height === null ? '' : Number(settingsForm.height),
  weight: settingsForm.weight === '' || settingsForm.weight === null ? '' : Number(settingsForm.weight),
  birthdate: settingsForm.birthdate || '',
  avatar: settingsForm.avatar || ''
}))

const currentSettingsSerialized = computed(() => JSON.stringify(normalizedSettings.value))

const isDirty = computed(() => currentSettingsSerialized.value !== settingsSnapshot.value)

const dirtyTagClass = computed(() => {
  return isDirty.value
    ? 'text-neon-orange border-neon-orange/40 bg-neon-orange/15'
    : 'text-neon-green border-neon-green/40 bg-neon-green/15'
})

const isValidMainlandPhone = (value) => {
  const text = String(value || '').trim()
  if (!text) return true
  return /^1[3-9]\d{9}$/.test(text)
}

const isValidAvatarHttpUrl = (value) => {
  const text = String(value || '').trim()
  if (!text) return true
  try {
    const url = new URL(text)
    return ['http:', 'https:'].includes(url.protocol)
  } catch (error) {
    return false
  }
}

const phoneValidationError = computed(() => {
  const text = String(settingsForm.phone || '').trim()
  if (!text) return ''
  if (isValidMainlandPhone(text)) return ''
  return '手机号格式不正确（需 11 位大陆手机号）'
})

const avatarValidationError = computed(() => {
  const text = String(settingsForm.avatar || '').trim()
  if (!text) return ''
  if (isValidAvatarHttpUrl(text)) return ''
  return '头像链接必须为 http/https 地址'
})

const avatarPreviewUrl = computed(() => {
  if (avatarValidationError.value) return ''
  return String(settingsForm.avatar || '').trim()
})

const displayText = (value) => {
  if (value === null || value === undefined) return '--'
  const text = String(value).trim()
  return text ? text : '--'
}

const displayNumber = (value, unit = '') => {
  if (value === null || value === undefined || value === '') return '--'
  return `${value}${unit ? ` ${unit}` : ''}`
}

const hasAnyProfileData = computed(() => {
  return [
    profile.username,
    profile.phone,
    profile.role,
    profile.gender,
    profile.height,
    profile.weight,
    profile.avatar
  ].some((v) => v !== null && v !== undefined && String(v).trim() !== '')
})

const applyProfileToSettingsForm = () => {
  settingsForm.phone = profile.phone || ''
  settingsForm.gender = profile.gender || ''
  settingsForm.height = profile.height ?? ''
  settingsForm.weight = profile.weight ?? ''
  settingsForm.birthdate = profile.birthdate || ''
  settingsForm.avatar = profile.avatar || ''
  avatarPreviewFailed.value = false
  settingsSnapshot.value = currentSettingsSerialized.value
}

const resetSettingsForm = () => {
  applyProfileToSettingsForm()
  settingsError.value = ''
}

const openSettingsDialog = () => {
  settingsError.value = ''
  isSettingsDialogOpen.value = true
}

const closeSettingsDialog = () => {
  isSettingsDialogOpen.value = false
}

const goMyPlan = () => {
  router.push('/my-plan')
}

const handlePhoneInput = () => {
  settingsForm.phone = String(settingsForm.phone || '').replace(/\D/g, '').slice(0, 11)
}

const refreshProfile = async () => {
  isLoadingProfile.value = true
  try {
    const data = await fetchUserProfile()

    profile.username = data.username ?? data.user_info?.username ?? ''
    profile.phone = data.phone ?? data.mobile ?? ''
    profile.role = data.role ?? data.user_info?.role ?? ''
    profile.gender = data.gender ?? data.user_info?.gender ?? ''
    profile.height = data.height ?? data.user_info?.height ?? null
    profile.weight = data.weight ?? data.user_info?.weight ?? null
    profile.avatar = data.avatar ?? ''
    profile.birthdate = data.birthdate ?? ''

    applyProfileToSettingsForm()

    if (hasAnyProfileData.value) {
      statusMessage.type = 'ok'
      statusMessage.text = '资料同步完成'
    } else {
      statusMessage.type = 'warning'
      statusMessage.text = '已连接账号中心，但当前资料为空'
    }
  } catch (error) {
    statusMessage.type = 'error'
    statusMessage.text = '资料同步失败，请稍后重试'
  } finally {
    isLoadingProfile.value = false
  }
}

const validateSettings = () => {
  settingsError.value = ''

  if (phoneValidationError.value) {
    settingsError.value = phoneValidationError.value
    return false
  }

  if (avatarValidationError.value) {
    settingsError.value = avatarValidationError.value
    return false
  }

  const hasHeight = settingsForm.height !== '' && settingsForm.height !== null
  const hasWeight = settingsForm.weight !== '' && settingsForm.weight !== null
  if (hasHeight) {
    const h = Number(settingsForm.height)
    if (!Number.isFinite(h) || h < 80 || h > 260) {
      settingsError.value = '身高范围应在 80-260 cm'
      return false
    }
  }
  if (hasWeight) {
    const w = Number(settingsForm.weight)
    if (!Number.isFinite(w) || w < 20 || w > 300) {
      settingsError.value = '体重范围应在 20-300 kg'
      return false
    }
  }
  if (settingsForm.birthdate && !/^\d{4}-\d{2}-\d{2}$/.test(settingsForm.birthdate)) {
    settingsError.value = '出生日期格式应为 YYYY-MM-DD'
    return false
  }
  return true
}

const saveProfileSettings = async () => {
  if (isSavingProfile.value || !isDirty.value) return
  if (!validateSettings()) return

  isSavingProfile.value = true
  settingsError.value = ''

  const prev = JSON.parse(settingsSnapshot.value || '{}')
  const current = normalizedSettings.value
  const payload = {}
  for (const key of Object.keys(current)) {
    if (current[key] !== (prev[key] ?? '')) {
      payload[key] = current[key]
    }
  }

  if (Object.keys(payload).length === 0) {
    isSavingProfile.value = false
    return
  }

  try {

watch(() => settingsForm.avatar, () => {
  avatarPreviewFailed.value = false
})
    const data = await updateUserProfile(payload)

    profile.phone = data.phone ?? ''
    profile.gender = data.gender ?? ''
    profile.height = data.height ?? null
    profile.weight = data.weight ?? null
    profile.avatar = data.avatar ?? ''
    profile.birthdate = data.birthdate ?? ''

    applyProfileToSettingsForm()
    isSettingsDialogOpen.value = false

    statusMessage.type = 'ok'
    statusMessage.text = '个人信息已更新'
  } catch (error) {
    settingsError.value = error?.data?.error || error?.message || '保存失败，请稍后重试'
    statusMessage.type = 'error'
    statusMessage.text = '个人信息保存失败'
  } finally {
    isSavingProfile.value = false
  }
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

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
      return await navigator.mediaDevices.getUserMedia({ video: preferred, audio: false })
    } catch (e) {
      console.warn('指定 Global Shutter Camera 失败，回退默认摄像头', e)
    }
  }

  return await navigator.mediaDevices.getUserMedia({ video: fallback, audio: false })
}

const cleanupFaceMedia = () => {
  if (activeTrack) activeTrack.stop()
  if (activeMedia) activeMedia.getTracks().forEach((item) => item.stop())
  activeTrack = null
  activeMedia = null
  if (faceVideoRef.value) {
    faceVideoRef.value.srcObject = null
  }
}

const captureFaceData = async () => {
  const canvas = document.createElement('canvas')
  let sourceW = 640
  let sourceH = 480
  let drawSource = null

  if (typeof ImageCapture !== 'undefined' && activeTrack) {
    const imageCapture = new ImageCapture(activeTrack)
    const bitmap = await imageCapture.grabFrame()
    sourceW = bitmap.width
    sourceH = bitmap.height
    drawSource = bitmap
  } else if (faceVideoRef.value) {
    sourceW = faceVideoRef.value.videoWidth || sourceW
    sourceH = faceVideoRef.value.videoHeight || sourceH
    drawSource = faceVideoRef.value
  }

  canvas.width = sourceW
  canvas.height = sourceH
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('canvas context unavailable')
  }
  if (!drawSource) {
    throw new Error('video source unavailable')
  }
  ctx.drawImage(drawSource, 0, 0, sourceW, sourceH)

  return canvas.toDataURL('image/jpeg', 0.85)
}

const stopFaceEnroll = () => {
  faceLoopActive.value = false
  if (isFaceBusy.value) {
    statusMessage.type = 'warning'
    statusMessage.text = '已停止人脸采集'
  }
}

const toggleFaceEnroll = async () => {
  if (isFaceBusy.value) {
    stopFaceEnroll()
    return
  }

  isFaceBusy.value = true
  faceLoopActive.value = true

  try {
    statusMessage.type = 'ok'
    statusMessage.text = '采集中，请正对摄像头...'

    activeMedia = await openCameraWithFallback()

    if (faceVideoRef.value) {
      faceVideoRef.value.srcObject = activeMedia
    }

    activeTrack = activeMedia.getVideoTracks()[0]

    while (faceLoopActive.value) {
      const faceData = await captureFaceData()
      const result = await registerFace(faceData)

      if (result?.code === 'ENROLL_SUCCESS') {
        faceFeedback.type = 'success'
        faceFeedback.title = '录入成功'
        faceFeedback.desc = result?.msg || '人脸特征绑定成功'
        statusMessage.type = 'ok'
        statusMessage.text = '人脸录入完成'
        const ttsText = String(result?.tts_text || '人脸特征录入成功').trim()
        if (ttsText && speakWithBackendTts) {
          await speakWithBackendTts(ttsText)
        }
        faceLoopActive.value = false
        break
      }

      if (['NO_FACE', 'TOO_FAR', 'NOT_FACING'].includes(result?.code)) {
        faceFeedback.type = 'warning'
        faceFeedback.title = '请调整姿态'
        faceFeedback.desc = result?.msg || '请正对摄像头并靠近一些'
        statusMessage.type = 'warning'
        statusMessage.text = '姿态未通过，正在继续采集...'
      } else if (result?.code === 'IMG_ERROR') {
        faceFeedback.type = 'error'
        faceFeedback.title = '图像异常'
        faceFeedback.desc = result?.msg || '图像质量不足，请重试'
        statusMessage.type = 'warning'
        statusMessage.text = '图像不够清晰，正在继续采集...'
      } else {
        faceFeedback.type = 'error'
        faceFeedback.title = '录入失败'
        faceFeedback.desc = result?.msg || '返回状态异常'
        statusMessage.type = 'warning'
        statusMessage.text = '暂未完成录入，正在继续采集...'
      }

      if (faceLoopActive.value) {
        await wait(800)
      }
    }
  } catch (error) {
    if (error?.data?.code === 'PARAMS_INVALID') {
      faceFeedback.type = 'error'
      faceFeedback.title = '采集异常'
      faceFeedback.desc = error?.data?.msg || '本次采集数据无效'
      statusMessage.type = 'error'
      statusMessage.text = '采集异常，请重新尝试'
      faceLoopActive.value = false
      return
    }

    statusMessage.type = 'error'
    statusMessage.text = '人脸录入失败，请检查摄像头权限后重试'
    faceFeedback.type = 'error'
    faceFeedback.title = '录入失败'
    faceFeedback.desc = error?.message || '请检查设备后重试'
    faceLoopActive.value = false
  } finally {
    cleanupFaceMedia()
    isFaceBusy.value = false
  }
}

const checkDevice = async () => {
  try {
    const media = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    media.getTracks().forEach((t) => t.stop())
    statusMessage.type = 'ok'
    statusMessage.text = '摄像头检测通过'
  } catch (error) {
    statusMessage.type = 'error'
    statusMessage.text = '摄像头不可用或权限被拒绝'
  }
}

const logout = () => {
  localStorage.removeItem('auth_token')
  sessionStorage.removeItem('welcome_voice_pending')
  sessionStorage.removeItem('login_context')
  sessionStorage.removeItem('plan_ready_toast')
  router.push('/')
}

onMounted(() => {
  refreshProfile()
})

onUnmounted(() => {
  faceLoopActive.value = false
  cleanupFaceMedia()
})
</script>
