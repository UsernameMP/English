package com.usernamemp.englishsprint;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Payment-provider-neutral commercial catalog. It describes saleable scopes only;
 * checkout and receipt verification belong to external provider adapters.
 */
public final class EntitlementProductCatalog {
    public static final class Product {
        public final String id;
        public final String provider;
        public final String billingType;
        public final boolean checkoutEnabled;
        public final List<String> packIds;
        public final String subject;
        public final int gradeMin;
        public final int gradeMax;

        Product(JSONObject json) {
            id = json.optString("id", "");
            provider = json.optString("provider", "");
            billingType = json.optString("billing_type", "");
            checkoutEnabled = json.optBoolean("checkout_enabled", false);
            List<String> ids = new ArrayList<>();
            JSONObject scope = json.optJSONObject("scope");
            subject = scope == null ? "" : scope.optString("subject", "");
            gradeMin = scope == null ? 1 : scope.optInt("grade_min", 1);
            gradeMax = scope == null ? 12 : scope.optInt("grade_max", 12);
            JSONArray array = scope == null ? null : scope.optJSONArray("pack_ids");
            if (array != null) for (int i = 0; i < array.length(); i++) ids.add(array.optString(i));
            packIds = Collections.unmodifiableList(ids);
        }
    }

    private final List<Product> products = new ArrayList<>();

    public EntitlementProductCatalog(Context context) {
        try {
            JSONObject root = new JSONObject(readAsset(context, "commerce/products.json"));
            JSONArray array = root.getJSONArray("products");
            for (int i = 0; i < array.length(); i++) products.add(new Product(array.getJSONObject(i)));
        } catch (Exception e) {
            throw new IllegalStateException("Product catalog failed to load", e);
        }
    }

    public List<Product> products() {
        return Collections.unmodifiableList(products);
    }

    public Product subscriptionForSubject(String subject) {
        for (Product product : products) {
            if ("subscription".equals(product.billingType) && subject.equals(product.subject)) return product;
        }
        return null;
    }

    private static String readAsset(Context context, String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
}
