/**
 * ZsysModules.java — JNA bindings for ZsysRouter and ZsysRegistry.
 *
 * Dependency (Maven):
 *   <dependency>
 *     <groupId>net.java.dev.jna</groupId>
 *     <artifactId>jna</artifactId>
 *     <version>5.14.0</version>
 *   </dependency>
 *
 * Usage:
 *   try (ZsysModules.Router r = new ZsysModules.Router()) {
 *       r.add("!hello", 42);
 *       int id = r.lookup("!hello");
 *   }
 */

package zsys.modules;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Memory;
import com.sun.jna.Pointer;

public final class ZsysModules {

    private ZsysModules() {}

    // ── JNA interface ──────────────────────────────────────────────────────

    interface NativeLib extends Library {
        // Router
        Pointer zsys_router_new();
        void    zsys_router_free(Pointer r);
        int     zsys_router_add(Pointer r, String trigger, int handler_id);
        int     zsys_router_remove(Pointer r, String trigger);
        int     zsys_router_lookup(Pointer r, String trigger);
        long    zsys_router_count(Pointer r);
        void    zsys_router_clear(Pointer r);

        // Registry
        Pointer zsys_registry_new();
        void    zsys_registry_free(Pointer reg);
        int     zsys_registry_register(Pointer reg, String name, int handler_id,
                                        String description, String category);
        int     zsys_registry_unregister(Pointer reg, String name);
        int     zsys_registry_get(Pointer reg, String name);
        int     zsys_registry_info(Pointer reg, String name,
                                    Memory out_desc, long desc_len,
                                    Memory out_cat,  long cat_len);
        long    zsys_registry_count(Pointer reg);
        Pointer zsys_registry_name_at(Pointer reg, long i);
    }

    private static final NativeLib LIB =
        Native.load("zsys_core", NativeLib.class);

    // ── exception ──────────────────────────────────────────────────────────

    /** Thrown when a zsys operation fails. */
    public static final class ZsysException extends RuntimeException {
        public ZsysException(String message) { super(message); }
    }

    // ── Router ─────────────────────────────────────────────────────────────

    /**
     * Trigger → handler_id open-addressing hash table.
     * Lookup is case-insensitive.
     * Implements {@link AutoCloseable} for use in try-with-resources.
     */
    public static final class Router implements AutoCloseable {
        private Pointer ptr;

        /** Create an empty Router. */
        public Router() {
            ptr = LIB.zsys_router_new();
            if (ptr == null)
                throw new ZsysException("zsys_router_new() returned null");
        }

        /** Add or update a trigger → handler_id mapping. */
        public void add(String trigger, int handlerId) {
            if (LIB.zsys_router_add(ptr, trigger, handlerId) != 0)
                throw new ZsysException("zsys_router_add failed for: " + trigger);
        }

        /**
         * Remove a trigger.
         * @return true if it existed, false otherwise.
         */
        public boolean remove(String trigger) {
            return LIB.zsys_router_remove(ptr, trigger) == 0;
        }

        /**
         * Look up handler_id for trigger (case-insensitive).
         * @return handler_id or -1 if not found.
         */
        public int lookup(String trigger) {
            return LIB.zsys_router_lookup(ptr, trigger);
        }

        /** Number of registered triggers. */
        public long count() {
            return LIB.zsys_router_count(ptr);
        }

        /** Remove all entries. */
        public void clear() {
            LIB.zsys_router_clear(ptr);
        }

        /** True if the trigger is registered. */
        public boolean contains(String trigger) {
            return lookup(trigger) != -1;
        }

        @Override
        public void close() {
            if (ptr != null) {
                LIB.zsys_router_free(ptr);
                ptr = null;
            }
        }
    }

    // ── Registry ───────────────────────────────────────────────────────────

    /** Metadata returned by {@link Registry#info}. */
    public static final class HandlerInfo {
        public final String description;
        public final String category;

        HandlerInfo(String description, String category) {
            this.description = description;
            this.category    = category;
        }

        @Override
        public String toString() {
            return "HandlerInfo{description='" + description
                 + "', category='" + category + "'}";
        }
    }

    /**
     * Dynamic array of name → handler_id entries with optional
     * description and category metadata.
     * Implements {@link AutoCloseable} for use in try-with-resources.
     */
    public static final class Registry implements AutoCloseable {
        private Pointer ptr;

        /** Create an empty Registry. */
        public Registry() {
            ptr = LIB.zsys_registry_new();
            if (ptr == null)
                throw new ZsysException("zsys_registry_new() returned null");
        }

        /**
         * Register a handler. Pass {@code null} for description/category to omit.
         */
        public void register(String name, int handlerId,
                             String description, String category) {
            if (LIB.zsys_registry_register(ptr, name, handlerId, description, category) != 0)
                throw new ZsysException("zsys_registry_register failed for: " + name);
        }

        /** Convenience overload with no description or category. */
        public void register(String name, int handlerId) {
            register(name, handlerId, null, null);
        }

        /**
         * Unregister by name.
         * @return true if it existed.
         */
        public boolean unregister(String name) {
            return LIB.zsys_registry_unregister(ptr, name) == 0;
        }

        /**
         * Return handler_id for name, or -1 if not found.
         */
        public int get(String name) {
            return LIB.zsys_registry_get(ptr, name);
        }

        /**
         * Return {@link HandlerInfo} for a registered name.
         * @throws ZsysException if not found.
         */
        public HandlerInfo info(String name) {
            Memory descBuf = new Memory(256);
            Memory catBuf  = new Memory(128);
            int rc = LIB.zsys_registry_info(ptr, name, descBuf, 256L, catBuf, 128L);
            if (rc != 0)
                throw new ZsysException("zsys_registry_info: not found: " + name);
            return new HandlerInfo(descBuf.getString(0), catBuf.getString(0));
        }

        /** Number of registered entries. */
        public long count() {
            return LIB.zsys_registry_count(ptr);
        }

        /**
         * Name at index {@code i}, or {@code null} if out of bounds.
         */
        public String nameAt(long i) {
            Pointer p = LIB.zsys_registry_name_at(ptr, i);
            return p == null ? null : p.getString(0);
        }

        /** All registered handler names. */
        public java.util.List<String> names() {
            long n = count();
            java.util.List<String> result = new java.util.ArrayList<>((int) n);
            for (long i = 0; i < n; i++) {
                String s = nameAt(i);
                if (s != null) result.add(s);
            }
            return result;
        }

        /** True if name is registered. */
        public boolean contains(String name) {
            return get(name) != -1;
        }

        @Override
        public void close() {
            if (ptr != null) {
                LIB.zsys_registry_free(ptr);
                ptr = null;
            }
        }
    }
}
