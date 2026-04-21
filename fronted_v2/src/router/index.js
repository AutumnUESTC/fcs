import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import UserLayout from '../layouts/UserLayout.vue'

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/pages/HomePage.vue')
      },
      {
        path: 'services',
        name: 'Services',
        component: () => import('../views/pages/ServicesPage.vue')
      },
      {
        path: 'about',
        name: 'About',
        component: () => import('../views/pages/AboutPage.vue')
      },
      {
        path: 'login',
        name: 'Login',
        component: () => import('../views/pages/LoginPage.vue')
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('../views/pages/RegisterPage.vue')
      }
    ]
  },
  {
    path: '/chat',
    component: UserLayout,
    children: [
      {
        path: '',
        name: 'Chat',
        component: () => import('../views/user/ChatPage.vue')
      },
      {
        path: 'user-center',
        name: 'UserCenter',
        component: () => import('../views/user/UserCenter.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/user/SettingsPage.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
