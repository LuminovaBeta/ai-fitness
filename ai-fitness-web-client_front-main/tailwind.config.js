/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 1. 专属色彩系统 (Apple Fitness 风格)
      colors: {
        kiosk: {
          bg: '#050507',       // 极深黑，让屏幕边框隐形
          card: '#141417',     // 略亮的深灰，用于非毛玻璃的卡片底色
        },
        neon: {
          green: '#32FF7E',    // 标志性荧光绿（行动、成功、状态好）
          orange: '#FF9F43',   // 活力橙（警告、中等强度）
          red: '#FF4D4D',      // 警示红（高心率、疲劳）
        },
        ai: {
          start: '#7B2CBF',    // 大模型发声时的渐变紫
          end: '#4361EE',      // 大模型发声时的渐变蓝
        }
      },
      // 2. 超大字体排版 (针对距离屏幕 1-1.5 米的体测场景)
      fontSize: {
        '8xl': ['6rem', { lineHeight: '1' }],
        '10xl': ['8rem', { lineHeight: '1' }],
        '12xl': ['12rem', { lineHeight: '1' }], // 用于显示心率、运动次数的超大数字
      },
      // 3. 字体族 (推荐使用科技感强的无衬线字体)
      fontFamily: {
        sans: ['"SF Pro Display"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"SF Mono"', 'ui-monospace', 'monospace'], // 数字显示推荐等宽字体，防止跳动
      },
      // 4. 为大模型语音预留动效
      animation: {
        'soundwave': 'soundwave 1s ease-in-out infinite',
        'breath': 'breath 2s ease-in-out infinite',
      },
      keyframes: {
        soundwave: {
          '0%, 100%': { transform: 'scaleY(0.5)' },
          '50%': { transform: 'scaleY(1)' },
        },
        breath: {
          '0%, 100%': { opacity: 0.5, transform: 'scale(0.95)' },
          '50%': { opacity: 1, transform: 'scale(1.05)' },
        }
      }
    },
  },
  plugins: [],
}