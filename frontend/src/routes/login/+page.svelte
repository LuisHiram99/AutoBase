<!-- src/routes/login/+page.svelte -->
<script lang="ts">
  import { enhance } from "$app/forms";
  export let form: any;
  export let data: { message?: string | null };
</script>

<section class="min-h-screen flex items-center justify-center bg-gray-300">
  <div class="w-full max-w-md bg-white rounded-2xl shadow p-8 space-y-6">
    <h1 class="text-2xl font-bold text-center text-gray-800">Iniciar sesión</h1>

    {#if data?.message}
      <p class="text-sm text-amber-600 text-center">
        {data.message}
      </p>
    {/if}

    {#if form?.error}
      <p class="text-sm text-red-600 text-center">
        {form.error}
      </p>
    {/if}

    <form method="POST" use:enhance class="space-y-4">
      <div>
        <label for="email" class="block text-sm font-medium text-gray-700">
          Correo electrónico
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          value={form?.values?.email ?? ""}
          class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium text-gray-700"> Contraseña </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        type="submit"
        class="w-full rounded-lg bg-blue-600 text-white py-2 text-sm font-semibold hover:bg-blue-700 transition"
      >
        Entrar
      </button>
    </form>
  </div>
</section>
