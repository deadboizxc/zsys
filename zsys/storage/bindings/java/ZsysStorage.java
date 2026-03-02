/**
 * Java JNA bindings for zsys/storage (ZsysKV key-value store).
 *
 * Add to pom.xml / build.gradle:
 *   com.sun.jna:jna:5.14.0
 *
 * Usage:
 * <pre>{@code
 *   try (ZsysStorage.KV kv = new ZsysStorage.KV()) {
 *       kv.set("hello", "world");
 *       System.out.println(kv.get("hello")); // world
 *   }
 * }</pre>
 */
package zsys.storage;

import com.sun.jna.*;
import com.sun.jna.ptr.PointerByReference;

import java.util.*;

public final class ZsysStorage {

    private ZsysStorage() {}

    // ── JNA library interface ─────────────────────────────────────────────

    /** Raw JNA mapping – use {@link KV} instead. */
    interface Lib extends Library {

        Lib INSTANCE = Native.load("zsys_storage", Lib.class);

        /** Callback invoked by zsys_kv_foreach. Return 0 to continue, non-zero to stop. */
        interface KVIterFn extends Callback {
            int invoke(String key, String value, Pointer ctx);
        }

        Pointer  zsys_kv_new      (long initialCap);
        void     zsys_kv_free     (Pointer kv);
        int      zsys_kv_set      (Pointer kv, String key, String value);
        String   zsys_kv_get      (Pointer kv, String key);
        int      zsys_kv_del      (Pointer kv, String key);
        int      zsys_kv_has      (Pointer kv, String key);
        long     zsys_kv_count    (Pointer kv);
        void     zsys_kv_clear    (Pointer kv);
        void     zsys_kv_foreach  (Pointer kv, KVIterFn fn, Pointer ctx);
        Pointer  zsys_kv_to_json  (Pointer kv);
        int      zsys_kv_from_json(Pointer kv, String json);
        void     zsys_free        (Pointer ptr);
    }

    // ── Safe Java wrapper ─────────────────────────────────────────────────

    /**
     * Thread-compatible (not thread-safe) wrapper around a native ZsysKV handle.
     * Implements {@link AutoCloseable} for use in try-with-resources.
     */
    public static final class KV implements AutoCloseable {

        private final Lib lib = Lib.INSTANCE;
        private Pointer ptr;

        /** Create a new, empty KV store with library-default capacity. */
        public KV() {
            this(0L);
        }

        /**
         * Create a new, empty KV store.
         *
         * @param initialCap Initial hash-table capacity (0 → default 16).
         */
        public KV(long initialCap) {
            ptr = lib.zsys_kv_new(initialCap);
            if (ptr == null) throw new OutOfMemoryError("zsys_kv_new returned null");
        }

        // ── Core operations ───────────────────────────────────────────────

        /**
         * Insert or update a key-value pair.
         *
         * @throws RuntimeException on allocation failure.
         */
        public void set(String key, String value) {
            int rc = lib.zsys_kv_set(ptr, key, value);
            if (rc != 0) throw new RuntimeException("zsys_kv_set: allocation failure");
        }

        /**
         * Retrieve a value by key.
         *
         * @return The value string, or {@code null} if not found.
         */
        public String get(String key) {
            return lib.zsys_kv_get(ptr, key);
        }

        /**
         * Retrieve a value by key, throwing if absent.
         *
         * @throws NoSuchElementException if the key is not present.
         */
        public String getOrThrow(String key) {
            String v = lib.zsys_kv_get(ptr, key);
            if (v == null) throw new NoSuchElementException("Key not found: '" + key + "'");
            return v;
        }

        /**
         * Delete a key.
         *
         * @throws NoSuchElementException if the key was not found.
         */
        public void del(String key) {
            int rc = lib.zsys_kv_del(ptr, key);
            if (rc != 0) throw new NoSuchElementException("Key not found: '" + key + "'");
        }

        /** Returns {@code true} if the key exists. */
        public boolean has(String key) {
            return lib.zsys_kv_has(ptr, key) == 1;
        }

        /** Number of entries in the store. */
        public long count() {
            return lib.zsys_kv_count(ptr);
        }

        /** Remove all entries. */
        public void clear() {
            lib.zsys_kv_clear(ptr);
        }

        // ── Iteration ─────────────────────────────────────────────────────

        /**
         * Iterate over all key-value pairs.
         * Return {@code false} from the callback to stop early.
         */
        public void forEach(java.util.function.BiFunction<String, String, Boolean> fn) {
            lib.zsys_kv_foreach(ptr,
                (key, value, ctx) -> fn.apply(key, value) ? 0 : 1,
                null);
        }

        /**
         * Collect all key-value pairs into an unmodifiable {@link Map}.
         */
        public Map<String, String> items() {
            Map<String, String> result = new LinkedHashMap<>();
            forEach((k, v) -> { result.put(k, v); return true; });
            return Collections.unmodifiableMap(result);
        }

        // ── Serialisation ─────────────────────────────────────────────────

        /**
         * Serialise the store to a JSON string.
         *
         * @throws RuntimeException on failure.
         */
        public String toJson() {
            Pointer raw = lib.zsys_kv_to_json(ptr);
            if (raw == null) throw new RuntimeException("zsys_kv_to_json failed");
            try {
                return raw.getString(0);
            } finally {
                lib.zsys_free(raw);
            }
        }

        /**
         * Deserialise and merge a JSON string into this store.
         *
         * @throws IllegalArgumentException on parse or allocation error.
         */
        public void fromJson(String json) {
            int rc = lib.zsys_kv_from_json(ptr, json);
            if (rc != 0)
                throw new IllegalArgumentException("zsys_kv_from_json: parse or allocation error");
        }

        // ── Lifecycle ─────────────────────────────────────────────────────

        @Override
        public void close() {
            if (ptr != null) {
                lib.zsys_kv_free(ptr);
                ptr = null;
            }
        }
    }
}
