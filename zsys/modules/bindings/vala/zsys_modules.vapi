/**
 * zsys_modules.vapi — Vala bindings for ZsysRouter and ZsysRegistry.
 *
 * Link with: -lzsys_core
 */

[CCode (cheader_filename = "zsys_core.h", cprefix = "zsys_")]
namespace Zsys {

    /**
     * Trigger → handler_id open-addressing hash table.
     * Lookup is case-insensitive.
     */
    [CCode (cname = "ZsysRouter", free_function = "zsys_router_free", has_type_id = false)]
    [Compact]
    public class Router {

        /** Create a new empty Router. */
        [CCode (cname = "zsys_router_new")]
        public Router ();

        /**
         * Add or update a trigger → handler_id mapping.
         * Returns 0 on success, -1 on error.
         */
        [CCode (cname = "zsys_router_add")]
        public int add (string trigger, int handler_id);

        /**
         * Remove a trigger.
         * Returns 0 on success, -1 if not found.
         */
        [CCode (cname = "zsys_router_remove")]
        public int remove (string trigger);

        /**
         * Look up handler_id for trigger (case-insensitive).
         * Returns handler_id or -1 if not found.
         */
        [CCode (cname = "zsys_router_lookup")]
        public int lookup (string trigger);

        /** Number of registered triggers. */
        [CCode (cname = "zsys_router_count")]
        public size_t count ();

        /** Remove all entries. */
        [CCode (cname = "zsys_router_clear")]
        public void clear ();
    }


    /**
     * Dynamic array of name → handler_id entries with optional
     * description and category metadata.
     */
    [CCode (cname = "ZsysRegistry", free_function = "zsys_registry_free", has_type_id = false)]
    [Compact]
    public class Registry {

        /** Create a new empty Registry. */
        [CCode (cname = "zsys_registry_new")]
        public Registry ();

        /**
         * Register a handler.
         * description and category may be null.
         * Returns 0 on success, -1 on error.
         */
        [CCode (cname = "zsys_registry_register")]
        public int register (string name, int handler_id,
                             string? description, string? category);

        /**
         * Unregister by name.
         * Returns 0 on success, -1 if not found.
         */
        [CCode (cname = "zsys_registry_unregister")]
        public int unregister (string name);

        /**
         * Return handler_id for name, or -1 if not found.
         */
        [CCode (cname = "zsys_registry_get")]
        public int get (string name);

        /**
         * Fill out_desc / out_cat buffers with the handler's metadata.
         * Returns 0 on success, -1 if not found.
         */
        [CCode (cname = "zsys_registry_info")]
        public int info (string name,
                         [CCode (array_length_pos = 3.1)] char[]? out_desc,
                         [CCode (array_length_pos = 5.1)] char[]? out_cat);

        /** Number of registered entries. */
        [CCode (cname = "zsys_registry_count")]
        public size_t count ();

        /**
         * Internal name string at index i, or null if out of bounds.
         * The returned pointer is valid for the lifetime of this Registry.
         */
        [CCode (cname = "zsys_registry_name_at")]
        public unowned string? name_at (size_t i);
    }
}
