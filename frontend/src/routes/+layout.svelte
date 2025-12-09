<script lang="ts">
  import "../app.css";
  import Sidebar from "$lib/components/Sidebar.svelte";
  import Hero from "$lib/components/Hero.svelte";

  export let data;
</script>

{#if data.isLoggedIn}
  <!-- AUTHENTICATED APP -->
  <div class="flex h-screen bg-white text-gray-800">
    <Sidebar />

    <div class="flex-1 ml-49 flex flex-col">
      <Hero empresa="Los Chinos" />
      <main class="flex-1 p-6 overflow-y-auto bg-gray-50">
        <slot />
      </main>
    </div>
  </div>
{:else}
  <!-- UNAUTHENTICATED: Allow login page to fully control layout and background -->
  <slot />
{/if}
