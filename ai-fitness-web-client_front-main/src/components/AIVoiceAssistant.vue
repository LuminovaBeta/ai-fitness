<template>
  <div v-if="isVisible" class="fixed bottom-8 left-2 z-50" data-voice-bubble-root>
    <div 
      class="voice-bubble group flex items-start gap-3 rounded-3xl backdrop-blur-xl border shadow-2xl relative overflow-hidden cursor-pointer transition-all duration-500 ease-[cubic-bezier(.2,.8,.2,1)]"
      :class="bubbleClass"
      @click.stop="emit('toggleExpand')"
    >
      <div 
        class="relative w-12 h-12 flex-shrink-0 flex items-center justify-center rounded-full transition-all duration-500 z-10"
        :class="isPlaying ? 'bg-gradient-to-tr from-ai-start to-ai-end shadow-[0_0_25px_rgba(123,44,191,0.8)]' : 'bg-gradient-to-tr from-ai-start/30 to-ai-end/30'"
      >
        <div v-if="isPlaying" class="absolute inset-0 rounded-full border-2 border-purple-400 animate-ping opacity-75"></div>
        <div v-if="!isPlaying" class="absolute inset-0 rounded-full border border-white/30 animate-breath"></div>

        <AudioLines v-if="isPlaying" class="w-6 h-6 text-white animate-pulse" stroke-width="2.5" />
        <Mic v-else class="w-6 h-6 text-white/80" stroke-width="2" />
      </div>

      <div class="flex-1 flex items-start justify-between z-10 pr-1 min-w-0 overflow-hidden">
        
        <div class="flex flex-col justify-center flex-1 pr-3 min-w-0">
          <span :class="['text-sm font-bold transition-all duration-300', collapsedMode ? 'text-white/90' : (isPlaying ? 'text-white' : 'text-white/80')]">
            AI 教练
          </span>
          <span :class="['text-xs tracking-wider transition-all duration-300 mt-0.5', isPlaying ? 'text-neon-green font-medium' : 'text-white/50 uppercase']">
            {{ collapsedMode ? (lingerActive ? '刚播报完成' : '点击展开上次回复') : (isPlaying ? '说话中...' : '已播报，点击查看完整内容') }}
          </span>
          <span v-if="speechText && !collapsedMode" class="text-xs mt-1 text-white/75 whitespace-pre-wrap break-words transition-all duration-500" :class="(isExpanded || isPlaying) ? 'max-h-[240px] overflow-y-auto pr-1 opacity-100' : 'line-clamp-4 opacity-90'">
            {{ speechText }}
          </span>
        </div>

        <div v-if="isPlaying" class="flex items-center gap-[3px] h-6 flex-shrink-0">
          <div v-for="i in 5" :key="i" 
               class="w-1.5 rounded-full bg-neon-green animate-soundwave origin-bottom"
               :style="{ animationDelay: `${i * 0.15}s`, height: `${Math.random() * 50 + 50}%` }">
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { Mic, AudioLines } from '@lucide/vue'
import { computed, defineProps } from 'vue'

const emit = defineEmits(['toggleExpand'])

const props = defineProps({
  isPlaying: {
    type: Boolean,
    default: false
  },
  isVisible: {
    type: Boolean,
    default: false
  },
  isExpanded: {
    type: Boolean,
    default: false
  },
  speechText: {
    type: String,
    default: ''
  },
  lingerActive: {
    type: Boolean,
    default: false
  }
})

const collapsedMode = computed(() => !props.isPlaying && !props.isExpanded)

const bubbleClass = computed(() => {
  if (props.isExpanded) {
    return 'bg-black/85 border-ai-start/50 w-[500px] max-w-[min(560px,90vw)] p-4 translate-x-2 scale-[1.01]'
  }

  if (props.isPlaying) {
    return 'bg-black/90 border-ai-start/60 w-[420px] max-w-[min(520px,88vw)] p-4 translate-x-2 scale-[1.02]'
  }

  if (props.lingerActive) {
    return 'bg-black/75 border-ai-start/40 w-[360px] max-w-[min(500px,85vw)] p-3.5 translate-x-2'
  }

  return 'bg-white/8 border-white/15 w-[212px] p-3 hover:w-[236px] hover:border-white/25 hover:bg-white/10 hover:-translate-y-0.5'
})
</script>

<style scoped>
.animate-soundwave {
  animation: soundwave 0.8s ease-in-out infinite;
}

.voice-bubble {
  transform-origin: left bottom;
}
</style>