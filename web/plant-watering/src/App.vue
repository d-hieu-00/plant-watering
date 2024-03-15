<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
    <div class="container pl-5">
      <img alt="Monitor logo" class="logo" src="@/assets/logo.png" width="125" height="125" />
      <!-- <nav>
        <RouterLink to="/">Monitor Char</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav> -->
      <div class="card shadow" style="margin-top: 10px;">
        <div class="card-body">
          <p class="fw-semibold">Công nghệ máy tính hiện đại</p>
          <p>IT2004.CH1801</p>
          <ul>
            <li>Nguyễn Duy Hiệu</li>
            <li>Nguyễn Thị Kim Yến</li>
            <li>Nguyễn Quang Huy</li>
            <li>Phạm Hồ Quang Cảnh</li>
          </ul>
        </div>
      </div>
      <div class="card shadow " style="margin-top: 20px;">
        <div class="card-body">
          <p class="fw-semibold">Nông nghiệp thông minh</p>
          <p>Mô hình tự động tưới cây kết hợp với Machine Learning</p>
        </div>
      </div>
    </div>

  <RouterView />
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
</style>
