import { withSupabase } from "jsr:@supabase/server@1";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-admin-token",
  "Access-Control-Allow-Methods":
    "GET, POST, PUT, PATCH, DELETE, OPTIONS",
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store"
};

const TOKEN_EXPIRES_MS = 365 * 24 * 60 * 60 * 1000;

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...CORS_HEADERS,
      ...extraHeaders
    }
  });
}

function base64urlEncode(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function base64urlDecode(value) {
  const normalized =
    value.replace(/-/g, "+").replace(/_/g, "/") +
    "=".repeat((4 - (value.length % 4)) % 4);

  const binary = atob(normalized);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  return new TextDecoder().decode(bytes);
}

function constantTimeEqual(a, b) {
  let aStr = typeof a === "string" ? a : "";
  let bStr = typeof b === "string" ? b : "";

  if (aStr.length !== bStr.length) {
    return false;
  }

  let result = 0;

  for (let i = 0; i < aStr.length; i++) {
    result |= aStr.charCodeAt(i) ^ bStr.charCodeAt(i);
  }

  return result === 0;
}

function getTokenSecret() {
  const primary = Deno.env.get("CATALOG_TOKEN_SECRET");
  const fallback = Deno.env.get("CATALOG_ADMIN_KEY");
  const secret = primary ? primary : fallback;
  return secret ? secret : "";
}

async function signToken(username, role) {
  const finalRole = role ? role : "ADMIN";
  const secret = getTokenSecret();

  if (!secret) {
    throw new Error("TOKEN_SECRET_NOT_CONFIGURED");
  }

  const header = base64urlEncode(
    JSON.stringify({
      alg: "HS256",
      typ: "CATALOG_ADMIN"
    })
  );

  const payload = base64urlEncode(
    JSON.stringify({
      username: username,
      role: finalRole,
      iat: Date.now(),
      exp: Date.now() + TOKEN_EXPIRES_MS
    })
  );

  const unsigned = header + "." + payload;

  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    {
      name: "HMAC",
      hash: "SHA-256"
    },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(unsigned)
  );

  const signatureBytes = new Uint8Array(signature);
  let binary = "";

  for (const byte of signatureBytes) {
    binary += String.fromCharCode(byte);
  }

  const encodedSignature = btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");

  return unsigned + "." + encodedSignature;
}

async function verifyAdminToken(token) {
  try {
    let isValidToken = typeof token === "string";

    if (!isValidToken) {
      return null;
    }

    const parts = token.split(".");

    if (parts.length !== 3) {
      return null;
    }

    const header = parts[0];
    const payload = parts[1];
    const signature = parts[2];
    const secret = getTokenSecret();

    if (!secret) {
      return null;
    }

    const unsigned = header + "." + payload;

    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      {
        name: "HMAC",
        hash: "SHA-256"
      },
      false,
      ["sign"]
    );

    const expected = await crypto.subtle.sign(
      "HMAC",
      key,
      new TextEncoder().encode(unsigned)
    );

    const expectedBytes = new Uint8Array(expected);
    let binary = "";

    for (const byte of expectedBytes) {
      binary += String.fromCharCode(byte);
    }
const expectedSignature = btoa(binary)
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/g, "");
      if (!constantTimeEqual(signature, expectedSignature)) {
      return null;
    }

    const payloadData = JSON.parse(base64urlDecode(payload));

    if (!payloadData) {
      return null;
    }

    const allowedRoles = ["ADMIN", "OWNER", "MANAGER", "EMPLOYEE"];
    const roleOk = allowedRoles.includes(payloadData.role);

    if (!roleOk) {
      return null;
    }

    const usernameOk =
      typeof payloadData.username === "string" &&
      payloadData.username.length > 0;

    if (!usernameOk) {
      return null;
    }

    const expOk =
      Number.isFinite(payloadData.exp) &&
      payloadData.exp > Date.now();

    if (!expOk) {
      return null;
    }

    return payloadData;
  } catch {
    return null;
  }
}

function getAdminToken(req) {
  const customToken = req.headers.get("x-admin-token");
  const custom = customToken ? customToken : "";

  if (custom) {
    return custom.trim();
  }

  const authorization = req.headers.get("authorization");
  const auth = authorization ? authorization : "";

  if (auth.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim();
  }

  return "";
}

async function requireAdmin(req, ctx) {
  if (ctx.authMode === "secret") {
    return {
      authorized: true,
      user: {
        username: "service",
        role: "SERVICE"
      }
    };
  }

  const token = getAdminToken(req);

  if (!token) {
    return {
      authorized: false,
      user: null
    };
  }

  const tokenData = await verifyAdminToken(token);

  if (!tokenData) {
    return {
      authorized: false,
      user: null
    };
  }

  return {
    authorized: true,
    user: {
      username: tokenData.username,
      role: tokenData.role
    }
  };
}

function normalizeProductInput(body) {
  const isObject = body && typeof body === "object";

  if (!isObject) {
    return null;
  }

  const name =
    typeof body.name === "string" ? body.name.trim() : "";

  let price = "";

  if (typeof body.price === "string") {
    price = body.price.trim();
  } else if (typeof body.price === "number") {
    price = String(body.price).trim();
  }

  if (!name || !price) {
    return null;
  }

  let oldPrice = "";

  if (body.old_price !== undefined && body.old_price !== null) {
    oldPrice = String(body.old_price).trim();
  }

  const image =
    typeof body.image === "string" ? body.image.trim() : "";

  let category = "عام";

  if (typeof body.category === "string" && body.category.trim()) {
    category = body.category.trim();
  }

  const description =
    typeof body.description === "string"
      ? body.description.trim()
      : "";

  const published = body.published !== false;

  return {
    name: name,
    price: price,
    old_price: oldPrice,
    image: image,
    category: category,
    description: description,
    published: published
  };
}

function getProductId(parts) {
  const index = parts.indexOf("products");

  if (index === -1) {
    return null;
  }

  const value = parts[index + 1];
  const valueOk = value && /^\d+$/.test(value);

  if (!valueOk) {
    return null;
  }

  const id = Number(value);
  const idOk = Number.isSafeInteger(id) && id > 0;

  if (!idOk) {
    return null;
  }

  return id;
}

async function getPublishedProducts(ctx) {
  const result = await ctx.supabase
    .from("products")
    .select("*")
    .eq("published", true)
    .order("id", { ascending: true });

  if (result.error) {
    throw new Error("PRODUCTS_READ_ERROR: " + result.error.message);
  }

  return result.data ? result.data : [];
}

async function getAllProducts(ctx) {
  const result = await ctx.supabaseAdmin
    .from("products")
    .select("*")
    .order("id", { ascending: true });

  if (result.error) {
    throw new Error("PRODUCTS_ADMIN_READ_ERROR: " + result.error.message);
  }

  return result.data ? result.data : [];
}
async function hashPassword(password, salt) {
  const data = new TextEncoder().encode(salt + ":" + password + ":" + salt);
  const buf = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(buf);
  let hex = "";
  for (let i = 0; i < bytes.length; i++) {
    hex += bytes[i].toString(16).padStart(2, "0");
  }

  return hex;
}

export default {
  fetch: withSupabase(
    {
      auth: ["publishable", "secret"]
    },

    async (req, ctx) => {
      try {
        if (req.method === "OPTIONS") {
          return new Response(null, {
            status: 204,
            headers: CORS_HEADERS
          });
        }

        const url = new URL(req.url);
        const parts = url.pathname.split("/").filter(Boolean);
        const authIndex = parts.indexOf("auth");

        const isLogin =
          req.method === "POST" &&
          authIndex !== -1 &&
          parts[authIndex + 1] === "login";

        // =====================================
        // ADMIN LOGIN
        // =====================================

        if (isLogin) {
          const body = await req.json().catch(() => null);
          const bodyOk = body && typeof body === "object";

          if (!bodyOk) {
            return json(
              {
                success: false,
                error: "بيانات تسجيل الدخول غير صالحة"
              },
              400
            );
          }

          const username =
            typeof body.username === "string"
              ? body.username.trim()
              : "";

          const password =
            typeof body.password === "string"
              ? body.password
              : "";

          if (!username) {
            return json(
              {
                success: false,
                error: "اسم المستخدم مطلوب"
              },
              400
            );
          }

          if (!password) {
            return json(
              {
                success: false,
                error: "كلمة المرور مطلوبة"
              },
              400
            );
          }

          let authenticated = false;
          let userRole = "EMPLOYEE";
          let userName = username;

          // ═══ 1) فحص المالك (env vars) ═══
          const envUser = Deno.env.get("CATALOG_ADMIN_USERNAME");
          const configuredUsername = envUser ? envUser : "";

          const envPass = Deno.env.get("CATALOG_ADMIN_PASSWORD");
          const configuredPassword = envPass ? envPass : "";

          const hasEnvCreds =
            configuredUsername.length > 0 &&
            configuredPassword.length > 0;

          if (hasEnvCreds) {
            const usernameValid = constantTimeEqual(
              username,
              configuredUsername
            );

            const passwordValid = constantTimeEqual(
              password,
              configuredPassword
            );

            const bothValid = usernameValid && passwordValid;

            if (bothValid) {
              authenticated = true;
              userRole = "OWNER";
              userName = "المسؤول الرئيسي";
            }
          }

          // ═══ 2) فحص جدول app_users ═══
          if (!authenticated) {
            const userResult = await ctx.supabaseAdmin
              .from("app_users")
              .select("*")
              .eq("username", username)
              .eq("active", true)
              .maybeSingle();

            if (userResult.data) {
              const user = userResult.data;
              let valid = false;

              const hasHash = user.password_hash && user.salt;

              if (hasHash) {
                const computed = await hashPassword(
                  password,
                  user.salt
                );
                valid = computed === user.password_hash;
              } else if (user.password) {
                valid = user.password === password;
              }
if (valid) {
                authenticated = true;
                userRole = user.role ? user.role : "EMPLOYEE";
                userName = user.name ? user.name : username;
              }
            }
          }

          if (!authenticated) {
            return json(
              {
                success: false,
                error: "اسم المستخدم أو كلمة المرور غير صحيحة"
              },
              401
            );
          }

          const token = await signToken(username, userRole);

          return json({
            success: true,
            user: {
              username: username,
              role: userRole,
              name: userName
            },
            token: token,
            expiresIn: TOKEN_EXPIRES_MS / 1000
          });
        }

        // =====================================
        // PUBLIC PRODUCTS
        // =====================================

        const isPublicProducts =
          req.method === "GET" &&
          parts.includes("products") &&
          !parts.includes("all");

        if (isPublicProducts) {
          const products = await getPublishedProducts(ctx);

          return json({
            success: true,
            products: products
          });
        }

        // =====================================
        // ADMIN AUTHORIZATION
        // =====================================

        const auth = await requireAdmin(req, ctx);

        if (!auth.authorized) {
          return json(
            {
              success: false,
              error: "Admin authorization required"
            },
            401
          );
        }

        // =====================================
        // GET ALL PRODUCTS FOR ADMIN
        // =====================================

        const isAdminAll =
          req.method === "GET" &&
          parts.includes("products") &&
          parts.includes("all");

        if (isAdminAll) {
          const products = await getAllProducts(ctx);

          return json({
            success: true,
            products: products
          });
        }

        const productId = getProductId(parts);

        // =====================================
        // ADD PRODUCT
        // =====================================

        if (req.method === "POST") {
          if (!parts.includes("products")) {
            return json(
              {
                success: false,
                error: "Invalid endpoint"
              },
              404
            );
          }

          const body = await req.json().catch(() => null);
          const product = normalizeProductInput(body);

          if (!product) {
            return json(
              {
                success: false,
                error: "name and price are required"
              },
              400
            );
          }

          const result = await ctx.supabaseAdmin
            .from("products")
            .insert(product)
            .select("*")
            .single();

          if (result.error) {
            console.error(
              "PRODUCT_CREATE_ERROR:",
              result.error.message
            );

            return json(
              {
                success: false,
                error: "تعذر إضافة المنتج"
              },
              500
            );
          }

          return json(
            {
              success: true,
              product: result.data
            },
            201
          );
        }

        // =====================================
        // UPDATE PRODUCT
        // =====================================

        if (req.method === "PUT") {
          if (!productId) {
            return json(
              {
                success: false,
                error: "Product ID is required"
              },
              400
            );
          }

          const body = await req.json().catch(() => null);
          const product = normalizeProductInput(body);
if (!product) {
            return json(
              {
                success: false,
                error: "name and price are required"
              },
              400
            );
          }

          const result = await ctx.supabaseAdmin
            .from("products")
            .update({
              ...product,
              updated_at: new Date().toISOString()
            })
            .eq("id", productId)
            .select("*")
            .single();

          if (result.error) {
            console.error(
              "PRODUCT_UPDATE_ERROR:",
              result.error.message
            );

            return json(
              {
                success: false,
                error: "تعذر تعديل المنتج"
              },
              500
            );
          }

          return json({
            success: true,
            product: result.data
          });
        }

        // =====================================
        // PUBLISH / UNPUBLISH PRODUCT
        // =====================================

        if (req.method === "PATCH") {
          if (!productId) {
            return json(
              {
                success: false,
                error: "Product ID is required"
              },
              400
            );
          }

          const body = await req.json().catch(() => null);
          const hasBoolean =
            body && typeof body.published === "boolean";

          if (!hasBoolean) {
            return json(
              {
                success: false,
                error: "published must be boolean"
              },
              400
            );
          }

          const result = await ctx.supabaseAdmin
            .from("products")
            .update({
              published: body.published,
              updated_at: new Date().toISOString()
            })
            .eq("id", productId)
            .select("*")
            .single();

          if (result.error) {
            console.error(
              "PRODUCT_PUBLISH_ERROR:",
              result.error.message
            );

            return json(
              {
                success: false,
                error: "تعذر تغيير حالة المنتج"
              },
              500
            );
          }

          return json({
            success: true,
            product: result.data
          });
        }

        // =====================================
        // DELETE PRODUCT
        // =====================================

        if (req.method === "DELETE") {
          if (!productId) {
            return json(
              {
                success: false,
                error: "Product ID is required"
              },
              400
            );
          }

          const result = await ctx.supabaseAdmin
            .from("products")
            .delete()
            .eq("id", productId)
            .select("*")
            .single();

          if (result.error) {
            console.error(
              "PRODUCT_DELETE_ERROR:",
              result.error.message
            );

            return json(
              {
                success: false,
                error: "تعذر حذف المنتج"
              },
              500
            );
          }

          return json({
            success: true,
            product: result.data
          });
        }

        return json(
          {
            success: false,
            error: "Method not allowed"
          },
          405
        );

      } catch (error) {
        const errMsg =
          error instanceof Error
            ? error.message
            : "Unknown error";

        console.error("SMART_WORKER_ERROR:", errMsg);

        return json(
          {
            success: false,
            error: "Internal server error"
          },
          500
        );
      }
    }
  )
};
