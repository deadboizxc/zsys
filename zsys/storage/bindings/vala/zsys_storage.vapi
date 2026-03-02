/**
 * Vala bindings for zsys/storage (ZsysKV key-value store).
 *
 * Compile with:
 *   valac --vapidir=. --pkg zsys_storage your_file.vala -X -lzsys_storage
 */

[CCode (cheader_filename = "../../c/include/zsys_storage.h", cprefix = "zsys_")]
namespace ZsysStorage {

    /**
     * Callback for KV.foreach().
     *
     * @param key   Current key (do not free).
     * @param value Current value (do not free).
     * @param ctx   User-supplied context.
     * @return 0 to continue, non-zero to stop.
     */
    [CCode (cname = "ZsysKVIterFn", has_target = false)]
    public delegate int KVIterFn (string key, string value, void* ctx);

    /**
     * Opaque in-memory key-value store.
     *
     * Usage:
     * {{{
     *   var kv = new ZsysStorage.KV (0);
     *   kv.set ("hello", "world");
     *   print (kv.get ("hello")); // "world"
     * }}}
     */
    [Compact]
    [CCode (cname = "ZsysKV", free_function = "zsys_kv_free", cprefix = "zsys_kv_")]
    public class KV {

        /**
         * Create a new, empty KV store.
         *
         * @param initial_cap Initial hash-table capacity (0 → default 16).
         */
        [CCode (cname = "zsys_kv_new")]
        public KV (size_t initial_cap = 0);

        /**
         * Insert or update a key-value pair.
         *
         * @return 0 on success, -1 on allocation failure.
         */
        public int set (string key, string value);

        /**
         * Look up a value by key.
         *
         * @return Internal pointer to value, or null if not found.
         */
        [CCode (array_null_terminated = false)]
        public unowned string? get (string key);

        /**
         * Delete a key.
         *
         * @return 0 if deleted, -1 if not found.
         */
        public int del (string key);

        /**
         * Check whether a key exists.
         *
         * @return 1 if present, 0 otherwise.
         */
        public int has (string key);

        /**
         * Number of entries currently in the store.
         */
        public size_t count ();

        /**
         * Remove all entries.
         */
        public void clear ();

        /**
         * Iterate over all key-value pairs in undefined order.
         */
        public void @foreach (KVIterFn fn, void* ctx = null);

        /**
         * Serialise the store to a JSON string.
         * The returned string must be freed with ZsysStorage.free().
         */
        [CCode (cname = "zsys_kv_to_json")]
        public string? to_json ();

        /**
         * Deserialise and merge a JSON string into this store.
         *
         * @return 0 on success, -1 on error.
         */
        [CCode (cname = "zsys_kv_from_json")]
        public int from_json (string json);
    }

    /**
     * Free a pointer returned by zsys (e.g., from KV.to_json()).
     */
    [CCode (cname = "zsys_free")]
    public void free (void* ptr);
}
