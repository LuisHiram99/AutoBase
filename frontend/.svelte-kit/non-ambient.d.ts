
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/clientes" | "/cuenta" | "/empleados" | "/login" | "/logout" | "/piezas" | "/talleres" | "/vehiculos";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/clientes": Record<string, never>;
			"/cuenta": Record<string, never>;
			"/empleados": Record<string, never>;
			"/login": Record<string, never>;
			"/logout": Record<string, never>;
			"/piezas": Record<string, never>;
			"/talleres": Record<string, never>;
			"/vehiculos": Record<string, never>
		};
		Pathname(): "/" | "/clientes" | "/clientes/" | "/cuenta" | "/cuenta/" | "/empleados" | "/empleados/" | "/login" | "/login/" | "/logout" | "/logout/" | "/piezas" | "/piezas/" | "/talleres" | "/talleres/" | "/vehiculos" | "/vehiculos/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/img/logo/logo-chinos.jpeg" | "/robots.txt" | string & {};
	}
}