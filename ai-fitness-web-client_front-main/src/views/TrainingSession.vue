<template>
  <div class="relative w-full h-full bg-black overflow-hidden text-white">
    <img
      v-if="poseStreamUrl"
      :src="poseStreamUrl"
      @load="onPoseStreamLoaded"
      @error="onPoseStreamError"
      class="absolute inset-0 w-full h-full object-cover"
      alt="pose stream"
    />
    <div v-else class="absolute inset-0 w-full h-full flex items-center justify-center text-gray-300">
      视频画面暂未就绪
    </div>
    <div v-if="poseStreamError" class="absolute inset-0 w-full h-full flex items-center justify-center text-red-300 bg-black/30 z-10 pointer-events-none">
      画面连接中断，请稍后重试或联系工作人员
    </div>

    <div class="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/40"></div>

    <div
      v-if="currentPhase === 'REST'"
      class="absolute inset-0 z-20 flex items-center justify-center bg-black/55 backdrop-blur-sm pointer-events-none"
    >
      <div class="text-center px-12 py-10 rounded-3xl border border-cyan-200/40 bg-black/45 shadow-2xl max-w-[720px]">
        <p class="text-cyan-200 text-lg tracking-[0.28em] font-semibold">REST</p>
        <p class="mt-3 text-7xl font-black">休息调整中</p>
        <p class="mt-5 text-4xl font-mono">剩余 {{ restRemainingSeconds }} 秒</p>
        <p class="mt-4 text-2xl text-cyan-100">放松肩颈，均匀呼吸，为下一组做准备。</p>
        <p class="mt-3 text-2xl text-neon-orange font-semibold" v-if="stableSampling.active && stableSampling.phase === 'REST'">
          请保持自然站立，{{ restSamplingRemainingSeconds }} 秒后完成恢复检测
        </p>
      </div>
    </div>

    <div
      v-if="isEndSampling"
      class="absolute inset-0 z-20 flex items-center justify-center bg-black/60 backdrop-blur-sm pointer-events-none"
    >
      <div class="text-center px-12 py-10 rounded-3xl border border-neon-orange/50 bg-black/50 shadow-2xl max-w-[760px]">
        <p class="text-neon-orange text-lg tracking-[0.28em] font-semibold">END</p>
        <p class="mt-3 text-7xl font-black">训练收尾中</p>
        <p class="mt-5 text-4xl font-mono">剩余 {{ endSamplingRemainingSeconds }} 秒</p>
        <p class="mt-4 text-2xl text-gray-100">请保持自然站立，系统正在记录训练后的身体状态。</p>
      </div>
    </div>

    <div class="absolute top-6 left-6 right-6 flex items-start justify-between z-10">
      <div class="glass-panel rounded-2xl p-4 min-w-[280px]">
        <p class="text-sm text-gray-300 tracking-wider">实时体征</p>
        <p class="text-3xl font-mono font-bold mt-2 text-neon-red">{{ metrics.heartRate }} bpm</p>
        <p class="text-xl font-mono mt-1 text-neon-green">SpO₂ {{ metrics.spo2 }}%</p>
        <p v-if="currentPhase === 'REST'" class="mt-3 text-lg text-cyan-200 font-semibold">休息倒计时：{{ restRemainingSeconds }}s</p>
        <p v-if="currentPhase === 'REST' && stableSampling.active" class="mt-2 text-lg text-neon-orange font-semibold">恢复检测倒计时：{{ restSamplingRemainingSeconds }}s</p>
        <p v-if="isEndSampling" class="mt-2 text-lg text-neon-orange font-semibold">训练收尾倒计时：{{ endSamplingRemainingSeconds }}s</p>
        <div v-if="rosStageText" class="mt-4 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
          <p class="text-[11px] text-gray-400 tracking-[0.22em]">阶段状态</p>
          <p class="mt-1 text-sm text-gray-200 leading-5">{{ rosStageText }}</p>
        </div>
      </div>

      <div class="glass-panel-light rounded-2xl p-5 text-right min-w-[320px]">
        <p class="text-sm text-gray-300 tracking-wider">训练进度（累计）</p>
        <p class="text-5xl font-black tracking-tighter mt-1">{{ currentRep }} / {{ totalTargetReps }}</p>
        <p class="text-base text-gray-300 mt-1">第 {{ currentSet }} 组 / 共 {{ totalSets }} 组 · 每组 {{ repsPerSet }} 次</p>
      </div>
    </div>

    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 w-[72%]">
      <div class="glass-panel-light rounded-3xl px-8 py-5 flex items-center justify-between">
        <div>
          <p class="text-sm text-gray-300 tracking-wider">AI 提示</p>
          <p class="text-2xl font-bold mt-1">{{ coachTip }}</p>
        </div>
        <div class="flex gap-3">
          <button
            @click="togglePause"
            class="px-5 py-3 rounded-xl bg-white/10 border border-white/20 hover:bg-white/15"
          >
            {{ isPaused ? '继续' : '暂停' }}
          </button>
          <button @click="goHome" class="px-5 py-3 rounded-xl bg-neon-red/30 border border-neon-red/50 hover:bg-neon-red/40">结束</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as ROSLIB from 'roslib'
import { fetchTrainSessionState, finishTrainSession, ingestTrainSessionRealtime, playTts } from '../api/train'
import { fetchRosRuntimeConfig } from '../api/runtime'

const router = useRouter()
const route = useRoute()
const stopVoice = inject('stopVoice')
const speakWithBackendTts = inject('speakWithBackendTts')

const poseStreamUrl = ref('')
const poseStreamError = ref(false)
const sessionId = ref(route.query.sessionId || '')

const totalSets = ref(Number(route.query.sets) || 3)
const currentSet = ref(1)
const repsPerSet = ref(Number(route.query.reps) || 20)
const totalTargetReps = ref(totalSets.value * repsPerSet.value)
const restSeconds = ref(Math.max(1, Number(route.query.restSec) || 45))
const currentRep = ref(0)
const isPaused = ref(false)
const coachTip = ref('保持核心收紧，动作速度均匀。')
const rosStageText = ref('')
const runtimeMode = ref('windows_debug')
const rosDebugMode = ref(true)
const sessionRealtimeSourceMode = ref('simulated')
const runtimeConfig = ref(null)
const activeExerciseCode = ref('')
const activeExerciseName = ref('')

const perceivedExertion = ref(3)
const errorCount = ref(0)

const metrics = reactive({
  heartRate: 102,
  spo2: 98
})

const sessionStartedAt = ref(0)
const phaseEnteredAt = ref(0)
const currentPhase = ref('WORK')
const stableSampling = reactive({
  active: false,
  phase: '',
  startedAt: 0,
  samples: []
})
const timeSeriesPayload = ref([])
const rosRepOffset = ref(0)
const lastRawRosRep = ref(0)

// ROS 实时链路（实机模式）
const rosConn = shallowRef(null)
const rosConnected = ref(false)
const rosTopics = {
  motionControl: null,
  motionState: null,
  motionRepCompleted: null,
  motionErrors: null,
  heartControl: null,
  heartRate: null,
  heartSpo2: null
}

const parseQueryExerciseCodes = () => {
  const codes = []
  const single = String(route.query.exercise || '').trim()
  if (single) codes.push(single)

  const raw = route.query.exercises
  if (Array.isArray(raw)) {
    raw.forEach((item) => {
      const code = String(item || '').trim()
      if (code) codes.push(code)
    })
  } else if (typeof raw === 'string') {
    raw.split(',').forEach((item) => {
      const code = String(item || '').trim()
      if (code) codes.push(code)
    })
  }

  return [...new Set(codes)]
}

const resolveFallbackMotionTopics = (cfg) => {
  const detectorList = Array.isArray(cfg?.action_detectors) ? cfg.action_detectors : []
  const firstDetectorTopics = detectorList[0]?.topics
  if (firstDetectorTopics && typeof firstDetectorTopics === 'object') {
    return firstDetectorTopics
  }

  const legacyTopics = cfg?.topics?.squat
  if (legacyTopics && typeof legacyTopics === 'object') {
    return legacyTopics
  }

  return {
    control: '',
    state: '',
    rep_completed: '',
    errors: ''
  }
}

const resolveActiveDetector = (cfg, preferredCodes = []) => {
  const detectorList = Array.isArray(cfg?.action_detectors) ? cfg.action_detectors : []
  const fallbackTopicCfg = resolveFallbackMotionTopics(cfg)
  const candidates = preferredCodes
    .map((item) => String(item || '').trim())
    .filter((item) => !!item)

  const detector = detectorList.find((item) => candidates.includes(String(item?.code || '')))
    || detectorList[0]

  const topicCfg = detector?.topics || fallbackTopicCfg
  activeExerciseCode.value = String(detector?.code || candidates[0] || activeExerciseCode.value || '')
  activeExerciseName.value = String(detector?.name_zh || detector?.name_en || activeExerciseCode.value)

  return topicCfg
}

let fakeTimer = null
let pollTimer = null
let ingestTimer = null
let restTimer = null
let endSamplingTimer = null
let phaseCountdownTimer = null
const isFinishing = ref(false)
const isEndSampling = ref(false)
const restRemainingSeconds = ref(0)
const endSamplingRemainingSeconds = ref(0)
const restSamplingRemainingSeconds = ref(0)
const restSamplingSeconds = ref(0)

const END_SAMPLING_SECONDS = 10

const SPEECH_PRIORITY = {
  AI: 1,
  REST: 2,
  COUNT: 3
}

const speakingPriority = ref(0)
const speakingToken = ref(0)
const lastCountVoiceAt = ref(0)
const lastSpokenAiTip = ref('')
const lastSpokenAiAt = ref(0)

const phaseLabelMap = {
  WORK: '动作进行中，保持节奏。',
  REST: '进入恢复时间，放松呼吸，准备下一组。',
  END: '训练即将完成，请保持自然站立。'
}

const normalizeSpeechText = (text) => String(text || '').replace(/\s+/g, ' ').trim()

const speakByPriority = async (text, priority = SPEECH_PRIORITY.AI) => {
  const normalizedText = normalizeSpeechText(text)
  if (!normalizedText) return

  // 低优先级不抢占高优先级
  if (priority < speakingPriority.value) return

  const token = speakingToken.value + 1
  speakingToken.value = token
  speakingPriority.value = priority

  // 抢占时先停止当前动效
  if (stopVoice) {
    stopVoice()
  }

  try {
    const ttsRes = speakWithBackendTts
      ? await speakWithBackendTts(normalizedText)
      : await playTts({ text: normalizedText })
    if (token !== speakingToken.value) return
  } catch {
    // 语音播报失败不影响训练主流程
  } finally {
    if (token === speakingToken.value) {
      speakingPriority.value = 0
    }
  }
}

const speakCountPriority = (repCount) => {
  const rep = Math.max(0, Number(repCount) || 0)
  if (rep <= 0) return

  const now = Date.now()
  // 限制最小间隔，防止消息风暴
  if (now - lastCountVoiceAt.value < 600) return
  lastCountVoiceAt.value = now

  speakByPriority(`第 ${rep} 次`, SPEECH_PRIORITY.COUNT)
}

const speakRestPriority = (text) => {
  speakByPriority(text, SPEECH_PRIORITY.REST)
}

const speakAiPriority = (text) => {
  const normalized = normalizeSpeechText(text)
  if (!normalized) return

  const now = Date.now()
  if (normalized === lastSpokenAiTip.value && now - lastSpokenAiAt.value < 3000) return
  lastSpokenAiTip.value = normalized
  lastSpokenAiAt.value = now

  speakByPriority(normalized, SPEECH_PRIORITY.AI)
}

const onPoseStreamLoaded = () => {
  poseStreamError.value = false
}

const onPoseStreamError = () => {
  poseStreamError.value = true
}

const syncStableSamplingByPhase = (phase) => {
  if (phase === 'REST' || phase === 'END') {
    if (phase === 'REST') {
      restSamplingSeconds.value = Math.max(1, Math.floor(restSeconds.value / 3))
      restSamplingRemainingSeconds.value = restSamplingSeconds.value
    }
    stableSampling.active = true
    stableSampling.phase = phase
    stableSampling.startedAt = Date.now()
    stableSampling.samples = []
  } else {
    stableSampling.active = false
    stableSampling.phase = ''
    stableSampling.startedAt = 0
    stableSampling.samples = []
  }
}

const clearRestTimer = () => {
  if (restTimer) {
    clearTimeout(restTimer)
    restTimer = null
  }
}

const clearEndSamplingTimer = () => {
  if (endSamplingTimer) {
    clearTimeout(endSamplingTimer)
    endSamplingTimer = null
  }
}

const clearPhaseCountdownTimer = () => {
  if (phaseCountdownTimer) {
    clearInterval(phaseCountdownTimer)
    phaseCountdownTimer = null
  }
}

const updatePhaseCountdown = () => {
  const now = Date.now()

  if (currentPhase.value === 'REST') {
    const restPassed = Math.floor((now - phaseEnteredAt.value) / 1000)
    restRemainingSeconds.value = Math.max(0, restSeconds.value - restPassed)

    if (stableSampling.active && stableSampling.phase === 'REST') {
      const restSamplingPassed = Math.floor((now - stableSampling.startedAt) / 1000)
      restSamplingRemainingSeconds.value = Math.max(0, restSamplingSeconds.value - restSamplingPassed)
    } else {
      restSamplingRemainingSeconds.value = 0
    }
  } else {
    restRemainingSeconds.value = 0
    restSamplingRemainingSeconds.value = 0
  }

  if (isEndSampling.value) {
    const endPassed = Math.floor((now - phaseEnteredAt.value) / 1000)
    endSamplingRemainingSeconds.value = Math.max(0, END_SAMPLING_SECONDS - endPassed)
  } else {
    endSamplingRemainingSeconds.value = 0
  }
}

const startPhaseCountdown = () => {
  clearPhaseCountdownTimer()
  updatePhaseCountdown()
  phaseCountdownTimer = setInterval(updatePhaseCountdown, 250)
}

const enterRestPhase = () => {
  clearRestTimer()
  currentPhase.value = 'REST'
  phaseEnteredAt.value = Date.now()
  const sec = Math.max(1, Number(restSeconds.value) || 45)
  restRemainingSeconds.value = sec
  restSamplingSeconds.value = Math.max(1, Math.floor(sec / 3))
  restSamplingRemainingSeconds.value = restSamplingSeconds.value
  syncStableSamplingByPhase('REST')

  // 休息阶段暂停深蹲节点，避免误动作继续累计次数
  if (!rosDebugMode.value && rosConnected.value) {
    // 仅停动作计数，心率/血氧继续采集
    publishMotionControl(false)
  }

  coachTip.value = '恢复时间到了，放松肩颈，均匀呼吸。'

  restTimer = setTimeout(() => {
    if (currentPhase.value === 'REST') {
      currentPhase.value = 'WORK'
      phaseEnteredAt.value = Date.now()
      syncStableSamplingByPhase('WORK')

      if (!rosDebugMode.value && rosConnected.value && !isPaused.value) {
        publishMotionControl(true)
      }

      coachTip.value = '状态已恢复，开始下一组动作。'
    }
    restTimer = null
  }, sec * 1000)
}

const beginEndSamplingThenFinish = () => {
  if (isEndSampling.value || isFinishing.value) return

  isEndSampling.value = true
  clearRestTimer()
  currentPhase.value = 'END'
  phaseEnteredAt.value = Date.now()
  endSamplingRemainingSeconds.value = END_SAMPLING_SECONDS
  syncStableSamplingByPhase('END')

  // 结束采样阶段：停止深蹲计数，保留心率血氧采集
  if (!rosDebugMode.value && rosConnected.value) {
    publishMotionControl(false)
  }

  coachTip.value = `训练目标已完成，请自然站立 ${END_SAMPLING_SECONDS} 秒，正在记录训练后状态。`

  clearEndSamplingTimer()
  endSamplingTimer = setTimeout(async () => {
    if (currentPhase.value === 'END') {
      coachTip.value = '记录完成，正在整理本次训练结果。'
    }

    // 结束采样后彻底停用节点并结算
    publishRosControl(false)
    await goHome({ forceFinalize: true })
    endSamplingTimer = null
  }, END_SAMPLING_SECONDS * 1000)
}

const hydrateRuntimeConfig = async () => {
  try {
    const cfg = await fetchRosRuntimeConfig()
    runtimeConfig.value = cfg
    runtimeMode.value = cfg?.runtime_mode || 'windows_debug'
    rosDebugMode.value = !!cfg?.debug_mode
    sessionRealtimeSourceMode.value = cfg?.session_realtime?.source_mode || 'simulated'
    poseStreamUrl.value = cfg?.active_profile?.mjpeg_stream_url || ''
    poseStreamError.value = false

    const topicCfg = resolveActiveDetector(cfg, parseQueryExerciseCodes())
    const topicState = topicCfg?.state || ''
    const topicHeartRate = cfg?.topics?.heart?.heart_rate || '/heart_sensor_node/heart_rate'
    const topicLlm = cfg?.topics?.llm?.output_string || '/rkllm/output_string'

    console.info('[TrainingSession][ROS Runtime]', {
      runtimeMode: runtimeMode.value,
      debugMode: rosDebugMode.value,
      dataSource: rosDebugMode.value ? 'mock/debug' : 'real/ros',
      topics: {
        exerciseCode: activeExerciseCode.value,
        exerciseName: activeExerciseName.value,
        control: topicCfg?.control,
        state: topicState,
        repCompleted: topicCfg?.rep_completed,
        errors: topicCfg?.errors,
        heartRate: topicHeartRate,
        llmOutput: topicLlm,
        poseImage: cfg?.topics?.pose_image || '/pose/image'
      },
      poseStreamUrl: poseStreamUrl.value
    })

    return cfg
  } catch (error) {
    runtimeConfig.value = null
    runtimeMode.value = 'windows_debug'
    rosDebugMode.value = true
    poseStreamUrl.value = ''
    poseStreamError.value = true

    console.warn('[TrainingSession][ROS Runtime] fallback to default windows_debug', {
      runtimeMode: runtimeMode.value,
      debugMode: rosDebugMode.value,
      dataSource: 'mock/debug',
      topics: {
        state: '',
        heartRate: '/heart_sensor_node/heart_rate',
        llmOutput: '/rkllm/output_string',
        poseImage: '/pose/image'
      },
      poseStreamUrl: '',
      error
    })

    return null
  }
}

const bindRosTopics = (cfg) => {
  if (!rosConn.value) return
  const topics = cfg?.topics || {}
  const motionTopicCfg = resolveActiveDetector(cfg, parseQueryExerciseCodes())
  const heartTopicCfg = topics.heart || {}

  const motionControlName = String(motionTopicCfg.control || '').trim()
  const motionStateName = String(motionTopicCfg.state || '').trim()
  const motionRepCompletedName = String(motionTopicCfg.rep_completed || '').trim()
  const motionErrorsName = String(motionTopicCfg.errors || '').trim()
  const heartControlName = String(heartTopicCfg.control || '/heart_sensor_node/control').trim()
  const heartRateName = String(heartTopicCfg.heart_rate || '/heart_sensor_node/heart_rate').trim()
  const heartSpo2Name = String(heartTopicCfg.spo2 || '/heart_sensor_node/spo2').trim()

  if (!motionControlName || !motionStateName || !motionRepCompletedName || !motionErrorsName) {
    coachTip.value = '动作识别暂未准备完成，请联系工作人员协助处理。'
  }

  rosTopics.motionControl = motionControlName ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: motionControlName,
    messageType: 'std_msgs/Bool'
  }) : null
  rosTopics.motionState = motionStateName ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: motionStateName,
    messageType: 'std_msgs/String'
  }) : null
  rosTopics.motionRepCompleted = motionRepCompletedName ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: motionRepCompletedName,
    messageType: 'std_msgs/Int32'
  }) : null
  rosTopics.motionErrors = motionErrorsName ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: motionErrorsName,
    messageType: 'std_msgs/String'
  }) : null

  rosTopics.heartControl = heartControlName ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: heartControlName,
    messageType: 'std_msgs/Bool'
  }) : null
  rosTopics.heartRate = heartRateName ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: heartRateName,
    messageType: 'std_msgs/Float32'
  }) : null
  rosTopics.heartSpo2 = heartSpo2Name ? new ROSLIB.Topic({
    ros: rosConn.value,
    name: heartSpo2Name,
    messageType: 'std_msgs/Float32'
  }) : null

  rosTopics.motionRepCompleted?.subscribe((msg) => {
    const rawRep = Math.max(0, Math.floor(Number(msg?.data) || 0))
    if (!Number.isFinite(rawRep)) return

    // 兼容节点重启/停用后计数从 0 重新开始的场景
    if (rawRep < lastRawRosRep.value && currentRep.value > 0) {
      rosRepOffset.value = currentRep.value
    }
    lastRawRosRep.value = rawRep

    const incomingRep = rosRepOffset.value + rawRep
    if (incomingRep < currentRep.value) return

    // 休息阶段不接受计数（通常已下发停用，这里做前端兜底）
    if (currentPhase.value === 'REST') return

    currentRep.value = Math.min(totalTargetReps.value, incomingRep)

    const eachSet = Math.max(1, repsPerSet.value)
    const completedSets = Math.floor(currentRep.value / eachSet)
    currentSet.value = Math.min(totalSets.value, Math.max(1, completedSets + 1))

    const isSetBoundary = currentRep.value > 0
      && currentRep.value < totalTargetReps.value
      && (currentRep.value % eachSet === 0)

    if (isSetBoundary) {
      enterRestPhase()
    } else {
      clearRestTimer()
      currentPhase.value = 'WORK'
      syncStableSamplingByPhase('WORK')
    }

    if (currentRep.value >= totalTargetReps.value) {
      beginEndSamplingThenFinish()
    }
  })

  rosTopics.heartRate?.subscribe((msg) => {
    if (typeof msg?.data === 'number') {
      metrics.heartRate = Math.max(0, Math.round(msg.data))
    }
  })

  rosTopics.heartSpo2?.subscribe((msg) => {
    if (typeof msg?.data === 'number') {
      metrics.spo2 = Math.max(0, Math.min(100, Number(msg.data.toFixed(1))))
    }
  })

  rosTopics.motionState?.subscribe((msg) => {
    let text = ''
    try {
      const parsed = JSON.parse(msg?.data || '{}')
      text = parsed?.msg || ''
    } catch {
      text = msg?.data || ''
    }
    if (text) {
      rosStageText.value = text
    }
  })

  rosTopics.motionErrors?.subscribe((msg) => {
    errorCount.value += 1
    try {
      const parsed = JSON.parse(msg?.data || '{}')
      if (parsed?.msg) {
        rosStageText.value = parsed.msg
        coachTip.value = `提示：${parsed.msg}`
      }
    } catch {
      if (msg?.data) {
        rosStageText.value = msg.data
        coachTip.value = `提示：${msg.data}`
      }
    }
  })
}

const publishRosControl = (enabled) => {
  try {
    rosTopics.motionControl?.publish({ data: !!enabled })
    rosTopics.heartControl?.publish({ data: !!enabled })
  } catch {
    // 忽略控制下发异常，前端仍可继续回退链路
  }
}

const publishMotionControl = (enabled) => {
  try {
    rosTopics.motionControl?.publish({ data: !!enabled })
  } catch {
    // 忽略控制下发异常
  }
}

const togglePause = () => {
  if (rosDebugMode.value) {
    isPaused.value = !isPaused.value
    coachTip.value = isPaused.value ? '训练已暂停，准备好后继续。' : '训练已继续，请保持动作标准。'
    return
  }

  if (!rosConnected.value) {
    coachTip.value = '当前连接暂不可用，请稍后再试。'
    return
  }

  if (isPaused.value) {
    publishRosControl(true)
    isPaused.value = false
    if (currentPhase.value !== 'REST') {
      coachTip.value = '训练已继续，请保持动作标准。'
    }
  } else {
    clearRestTimer()
    publishRosControl(false)
    isPaused.value = true
    coachTip.value = '训练已暂停，准备好后继续。'
  }
}

const disconnectRos = () => {
  try { rosTopics.motionState?.unsubscribe() } catch {}
  try { rosTopics.motionRepCompleted?.unsubscribe() } catch {}
  try { rosTopics.motionErrors?.unsubscribe() } catch {}
  try { rosTopics.heartRate?.unsubscribe() } catch {}
  try { rosTopics.heartSpo2?.unsubscribe() } catch {}

  publishRosControl(false)

  try { rosConn.value?.close() } catch {}
  rosConn.value = null
  rosConnected.value = false
}

const connectRosRealtime = (cfg) => {
  if (rosDebugMode.value) return false
  const rosbridgeUrl = cfg?.active_profile?.rosbridge_url
  if (!rosbridgeUrl) return false

  try {
    rosConn.value = new ROSLIB.Ros({ url: rosbridgeUrl })
    rosConn.value.on('connection', () => {
      rosConnected.value = true
      isPaused.value = false
      rosRepOffset.value = 0
      lastRawRosRep.value = 0
      try {
        bindRosTopics(cfg)
      } catch (error) {
        console.error('[TrainingSession][ROS] bindRosTopics failed:', error)
      }
      publishRosControl(true)
      coachTip.value = '实时识别已连接，动作与体征数据同步中。'
    })

    rosConn.value.on('error', () => {
      rosConnected.value = false
    })

    rosConn.value.on('close', () => {
      rosConnected.value = false
    })
    return true
  } catch {
    rosConnected.value = false
    return false
  }
}

const startMockData = () => {
  fakeTimer = setInterval(() => {
    if (currentRep.value < totalTargetReps.value) {
      currentRep.value += 1
      currentSet.value = Math.min(totalSets.value, Math.floor(currentRep.value / Math.max(1, repsPerSet.value)) + 1)
    } else {
      coachTip.value = '本次训练已完成，建议做几分钟拉伸放松。'
      speakAiPriority(coachTip.value)
    }

    metrics.heartRate = Math.min(165, metrics.heartRate + Math.round(Math.random() * 3 - 1))
    metrics.spo2 = Math.max(95, Math.min(100, metrics.spo2 + Math.round(Math.random() * 2 - 1)))
  }, 1600)
}

const stopMockData = () => {
  if (fakeTimer) {
    clearInterval(fakeTimer)
    fakeTimer = null
  }
}

const fetchSessionState = async () => {
  if (!sessionId.value) return

  try {
    const data = await fetchTrainSessionState(sessionId.value)

    if (runtimeConfig.value) {
      const sessionExercises = Array.isArray(data?.exercises) ? data.exercises : []
      const preferred = sessionExercises[0] || ''
      if (preferred && preferred !== activeExerciseCode.value) {
        resolveActiveDetector(runtimeConfig.value, sessionExercises)
      }
    }

    if (data.status === 'FINISHED') {
      stopPolling()
      disconnectRos()
      router.push('/home')
      return
    }

    const rosAuthoritative = !rosDebugMode.value

    totalSets.value = data.total_sets ?? totalSets.value

    if (!rosAuthoritative) {
      metrics.heartRate = data.heart_rate ?? metrics.heartRate
      metrics.spo2 = data.spo2 ?? metrics.spo2
      currentRep.value = data.current_rep ?? currentRep.value
      currentSet.value = data.current_set ?? currentSet.value
    }

    if (data.reps_per_set != null) {
      repsPerSet.value = Math.max(1, Number(data.reps_per_set) || repsPerSet.value)
    }

    if (data.target_reps != null || data.target_rep != null) {
      const incomingTargetReps = Number(data.target_reps ?? data.target_rep)
      if (Number.isFinite(incomingTargetReps) && incomingTargetReps > 0) {
        totalTargetReps.value = incomingTargetReps
      }
    }

    if ((data.reps_per_set == null) && totalSets.value > 0 && totalTargetReps.value > 0) {
      repsPerSet.value = Math.max(1, Math.ceil(totalTargetReps.value / totalSets.value))
    }

    if (!rosAuthoritative || data.phase === 'END') {
      const incomingTip = data.coach_message || phaseLabelMap[data.phase] || data.tip || coachTip.value
      coachTip.value = incomingTip
      if (data.tip) {
        rosStageText.value = data.tip
      }
    }

    let incomingPhase = currentPhase.value
    if (!rosAuthoritative) {
      incomingPhase = data.phase || currentPhase.value
    } else if (data.phase === 'END') {
      incomingPhase = 'END'
    }

    if (incomingPhase !== currentPhase.value) {
      clearRestTimer()
      currentPhase.value = incomingPhase
      phaseEnteredAt.value = Date.now()
      syncStableSamplingByPhase(incomingPhase)
    }

    if (stableSampling.active) {
      stableSampling.samples.push({
        ts: Date.now(),
        heart_rate: metrics.heartRate,
        spo2: metrics.spo2,
        current_rep: currentRep.value
      })

      const holdSecs = Math.floor((Date.now() - stableSampling.startedAt) / 1000)
      const requiredHoldSecs = stableSampling.phase === 'END'
        ? END_SAMPLING_SECONDS
        : Math.max(1, Math.floor(restSeconds.value / 3))
      if (holdSecs >= requiredHoldSecs) {
        const hrValues = stableSampling.samples.map((s) => s.heart_rate).filter((v) => Number.isFinite(v))
        const spo2Values = stableSampling.samples.map((s) => s.spo2).filter((v) => Number.isFinite(v))

        if (hrValues.length > 0 && spo2Values.length > 0) {
          const avgHr = Math.round(hrValues.reduce((a, b) => a + b, 0) / hrValues.length)
          const avgSpo2 = Math.round(spo2Values.reduce((a, b) => a + b, 0) / spo2Values.length)
          const offset = Math.max(0, Math.floor((Date.now() - sessionStartedAt.value) / 1000))

          const alreadyReported = timeSeriesPayload.value.some(
            (item) => item.phase === stableSampling.phase && Math.abs(item.offset - offset) <= 5
          )

          if (!alreadyReported) {
            timeSeriesPayload.value.push({
              offset,
              phase: stableSampling.phase,
              heart_rate: avgHr,
              spo2: avgSpo2,
              current_rep: currentRep.value,
              is_stable: true,
              hold_secs: requiredHoldSecs
            })
          }
        }

        stableSampling.active = false
        stableSampling.phase = ''
        stableSampling.startedAt = 0
        stableSampling.samples = []
      }
    }
  } catch {
    // 保持当前 UI，避免训练中断
  }
}

const startPolling = () => {
  if (!sessionId.value) return
  pollTimer = setInterval(fetchSessionState, 1000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const ingestRealtimeState = async () => {
  if (!sessionId.value) return
  if (rosDebugMode.value) return
  if (!rosConnected.value) return
  if (isPaused.value) return

  const progress = totalTargetReps.value > 0
    ? Math.max(0, Math.min(100, Number(((currentRep.value / totalTargetReps.value) * 100).toFixed(1))))
    : 0

  try {
    await ingestTrainSessionRealtime(sessionId.value, {
      phase: currentPhase.value,
      heart_rate: metrics.heartRate,
      spo2: metrics.spo2,
      current_rep: currentRep.value,
      current_set: currentSet.value,
      progress,
      coach_message: coachTip.value
    })
  } catch {
    // 上报失败不影响训练流程
  }
}

const startRealtimeIngest = () => {
  if (!sessionId.value) return
  if (rosDebugMode.value) return
  stopRealtimeIngest()
  ingestTimer = setInterval(ingestRealtimeState, 1000)
}

const stopRealtimeIngest = () => {
  if (ingestTimer) {
    clearInterval(ingestTimer)
    ingestTimer = null
  }
}

const finishSession = async () => {
  if (!sessionId.value || isFinishing.value) return
  isFinishing.value = true
  try {
    if (currentPhase.value === 'END' && stableSampling.active) {
      const holdSecs = Math.floor((Date.now() - stableSampling.startedAt) / 1000)
      if (holdSecs >= END_SAMPLING_SECONDS) {
        const hrValues = stableSampling.samples.map((s) => s.heart_rate).filter((v) => Number.isFinite(v))
        const spo2Values = stableSampling.samples.map((s) => s.spo2).filter((v) => Number.isFinite(v))
        if (hrValues.length > 0 && spo2Values.length > 0) {
          const offset = Math.max(0, Math.floor((Date.now() - sessionStartedAt.value) / 1000))
          timeSeriesPayload.value.push({
            offset,
            phase: 'END',
            heart_rate: Math.round(hrValues.reduce((a, b) => a + b, 0) / hrValues.length),
            spo2: Math.round(spo2Values.reduce((a, b) => a + b, 0) / spo2Values.length),
            current_rep: currentRep.value,
            is_stable: true,
            hold_secs: END_SAMPLING_SECONDS
          })
        }
      }
    }

    await finishTrainSession(sessionId.value, {
      reason: 'user_finish',
      final_reps: currentRep.value,
      perceived_exertion: perceivedExertion.value,
      error_count: errorCount.value,
      time_series: timeSeriesPayload.value
    })
  } catch {
    // 忽略结束请求失败，保证可返回主页
  } finally {
    isFinishing.value = false
  }
}

const goHome = async (options = {}) => {
  const forceFinalize = !!options.forceFinalize

  // 所有结束路径：先做 10s END 采样，再结算
  if (!forceFinalize && !isEndSampling.value && !isFinishing.value) {
    beginEndSamplingThenFinish()
    return
  }

  if (isFinishing.value) return
  isEndSampling.value = false
  clearEndSamplingTimer()
  isPaused.value = false
  stopPolling()
  stopRealtimeIngest()
  publishRosControl(false)
  await finishSession()
  disconnectRos()
  router.push('/home')
}

onMounted(() => {
  ;(async () => {
    const cfg = await hydrateRuntimeConfig()

    sessionStartedAt.value = Date.now()
    phaseEnteredAt.value = Date.now()
    startPhaseCountdown()

    connectRosRealtime(cfg)

    if (sessionId.value) {
      startPolling()
      startRealtimeIngest()
      fetchSessionState()
    } else if (!sessionId.value) {
      startMockData()
    }

    speakAiPriority('训练已开始，请保持动作标准。')
  })()
})

watch(currentRep, (nextRep, prevRep) => {
  const next = Number(nextRep) || 0
  const prev = Number(prevRep) || 0
  if (next > prev) {
    speakCountPriority(next)
  }
})

watch(currentPhase, (next, prev) => {
  if (next === prev) return
  if (next === 'REST') {
    const sec = Math.max(1, Number(restSeconds.value) || 45)
    speakRestPriority(`进入恢复时间，还有 ${sec} 秒，请放松呼吸。`)
    return
  }
  if (prev === 'REST' && next === 'WORK') {
    speakRestPriority('恢复完成，继续下一组训练。')
  }
})

onBeforeUnmount(() => {
  stopMockData()
  stopPolling()
  stopRealtimeIngest()
  clearRestTimer()
  clearEndSamplingTimer()
  clearPhaseCountdownTimer()
  disconnectRos()
  if (stopVoice) stopVoice()
})
</script>
