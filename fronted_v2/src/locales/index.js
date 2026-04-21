import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.js'
import en from './en.js'
import zhTW from './zh-TW.js'

const savedLanguage = localStorage.getItem('language') || 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: savedLanguage,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en': en,
    'zh-TW': zhTW
  }
})

export default i18n
