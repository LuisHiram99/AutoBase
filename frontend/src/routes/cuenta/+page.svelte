<script lang="ts">
  export let data;
  if (!data?.user) throw new Error("User data missing");

  const user = data.user;

  let first_name = user.first_name;
  let last_name = user.last_name;
  let email = user.email;
  let phone = "662-000-0000";
  let address = "Opcional";

  function updateProfile() {
    alert("Actualizar perfil se implementará cuando exista el endpoint.");
  }
</script>

<div class="bg-white p-6 rounded-lg shadow max-w-3xl mx-auto mt-4">
  <!-- HEADER -->
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-lg font-semibold text-gray-700">Datos personales</h2>

    <button class="p-1.5 border rounded-lg hover:bg-gray-100 transition" title="Descargar PDF">
      📄
    </button>
  </div>

  <hr class="mb-6 border-gray-300" />

  <!-- USER ROW -->
  <div class="flex items-center gap-4 mb-8">
    <!-- Avatar reducido -->
    <div class="w-20 h-20 rounded-full border flex items-center justify-center bg-gray-50">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="48"
        height="48"
        fill="#ccc"
        viewBox="0 0 24 24"
      >
        <path
          d="M12 12c2.761 0 5-2.239 5-5s-2.239-5-5-5-5 2.239-5 5 2.239 5 5 5zm0 2c-3.866 0-7 2.239-7 5v1h14v-1c0-2.761-3.134-5-7-5z"
        />
      </svg>
    </div>

    <!-- Info -->
    <div class="flex flex-col">
      <h3 class="text-xl font-semibold text-gray-800">
        {first_name}
        {last_name}
      </h3>
      <p class="text-gray-500 font-medium capitalize text-sm">{user.role}</p>
      <p class="text-gray-400 text-xs">Hermosillo</p>
    </div>
  </div>

  <!-- FORMULARIO COMPACTO -->
  <form on:submit|preventDefault={updateProfile} class="space-y-4">
    <!-- Usuario + botón -->
    <div class="grid grid-cols-12 items-center gap-3">
      <label class="col-span-3 text-gray-600 text-right text-sm">Usuario</label>

      <input
        class="col-span-6 p-2 border rounded bg-gray-100 text-gray-700 text-sm"
        value={user.email.split("@")[0]}
        disabled
      />

      <button
        type="button"
        class="col-span-3 px-3 py-1.5 bg-emerald-500 text-white rounded text-sm hover:bg-emerald-600"
      >
        Cambiar contraseña
      </button>
    </div>

    <!-- Teléfono -->
    <div class="grid grid-cols-12 items-center gap-3">
      <label class="col-span-3 text-gray-600 text-right text-sm">Teléfono</label>

      <input bind:value={phone} class="col-span-8 p-2 border rounded text-sm" />
    </div>

    <!-- Correo -->
    <div class="grid grid-cols-12 items-center gap-3">
      <label class="col-span-3 text-gray-600 text-right text-sm">Correo</label>

      <input bind:value={email} type="email" class="col-span-8 p-2 border rounded text-sm" />
    </div>

    <!-- Dirección -->
    <div class="grid grid-cols-12 items-start gap-3">
      <label class="col-span-3 text-gray-600 text-right text-sm mt-1">Dirección</label>

      <textarea bind:value={address} class="col-span-8 p-2 border rounded h-20 text-sm"></textarea>
    </div>

    <!-- BOTÓN ACTUALIZAR -->
    <div class="flex justify-end mt-4">
      <button
        type="submit"
        class="px-6 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition"
      >
        Actualizar
      </button>
    </div>
  </form>
</div>
