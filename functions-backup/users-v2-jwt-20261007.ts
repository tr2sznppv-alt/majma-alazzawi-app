import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-forwarded-for, x-real-ip",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
};

// JWT Utilities (HMAC-SHA256)
function bytesToBase64url(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function strToBase64url(str: string): string {
  return bytesToBase64url(new TextEncoder().encode(str));
}

function base64urlToStr(input: string): string {
  let b64 = input.replace(/-/g, "+").replace(/_/g, "/");
  while (b64.length % 4) b64 += "=";
  return atob(b64);
}

function base64urlToBytes(input: string): Uint8Array {
  let b64 = input.replace(/-/g, "+").replace(/_/g, "/");
  while (b64.length % 4) b64 += "=";
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function getHmacKey(secret: string): Promise<CryptoKey> {
  return await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

async function signJWT(payload: Record<string, unknown>, secret: string): Promise<string> {
  const header = { alg: "HS256", typ: "JWT" };
  const h = strToBase64url(JSON.stringify(header));
  const p = strToBase64url(JSON.stringify(payload));
  const data = h + "." + p;
  const key = await getHmacKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data));
  return data + "." + bytesToBase64url(new Uint8Array(sig));
}

async function verifyJWT(token: string, secret: string): Promise<Record<string, unknown> | null> {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const [h, p, s] = parts;
    const data = h + "." + p;
    const sigBytes = base64urlToBytes(s);
    const key = await getHmacKey(secret);
    const valid = await crypto.subtle.verify("HMAC", key, sigBytes, new TextEncoder().encode(data));
    if (!valid) return null;
    const payload = JSON.parse(base64urlToStr(p));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch (_e) {
    return null;
  }
}

async function hashPassword(password: string, salt: string): Promise<string> {
  const data = new TextEncoder().encode(salt + ":" + password + ":" + salt);
  const buf = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(buf);
  let hex = "";
  for (let i = 0; i < bytes.length; i++) hex += bytes[i].toString(16).padStart(2, "0");
  return hex;
}

function makeSalt(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  let hex = "";
  for (let i = 0; i < bytes.length; i++) hex += bytes[i].toString(16).padStart(2, "0");
  return hex;
}

function respond(data: unknown, status?: number): Response {
  const code = status === undefined ? 200 : status;
  const headers = Object.assign({}, cors, { "Content-Type": "application/json" });
  return new Response(JSON.stringify(data), { status: code, headers: headers });
}

function getClientIp(req: Request): string {
  let ip = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip");
  if (!ip) ip = "unknown";
  return ip;
}

function getUserAgent(req: Request): string {
  return req.headers.get("user-agent") || "unknown";
}

async function logAction(sb: any, req: Request, data: Record<string, unknown>) {
  try {
    await sb.from("audit_logs").insert({
      username: data.username || "unknown",
      action: data.action || "unknown",
      target_type: data.targetType || null,
      target_id: data.targetId || null,
      target_name: data.targetName || null,
      details: data.details || {},
      ip_address: getClientIp(req)
    });
  } catch (e) {
    console.warn("logAction failed:", e);
  }
}

type AuthResult = { ok: true; payload: Record<string, unknown> } | { ok: false; response: Response };

async function requireAuth(req: Request): Promise<AuthResult> {
  const authHeader = req.headers.get("authorization") || "";
  if (!authHeader.toLowerCase().startsWith("bearer ")) {
    return { ok: false, response: respond({ success: false, error: "unauthorized" }, 401) };
  }
  const token = authHeader.slice(7).trim();
  if (token.startsWith("sb_")) {
    return { ok: false, response: respond({ success: false, error: "unauthorized" }, 401) };
  }
  const secret = Deno.env.get("JWT_SECRET") || "";
  if (!secret) {
    return { ok: false, response: respond({ success: false, error: "server misconfigured" }, 500) };
  }
  const payload = await verifyJWT(token, secret);
  if (!payload) {
    return { ok: false, response: respond({ success: false, error: "invalid or expired token" }, 401) };
  }
  return { ok: true, payload };
}

async function requireOwner(req: Request): Promise<AuthResult> {
  const auth = await requireAuth(req);
  if (!auth.ok) return auth;
  if (auth.payload.role !== "OWNER") {
    return { ok: false, response: respond({ success: false, error: "forbidden" }, 403) };
  }
  return auth;
}

Deno.serve(async function(req) {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: cors });
  }

  try {
    const sb = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const url = new URL(req.url);
    const parts = url.pathname.split("/").filter(Boolean);
    const last = parts[parts.length - 1];

    // LOGIN: POST /users/login
    if (req.method === "POST" && url.pathname.endsWith("/login")) {
      const body = await req.json();
      const username = String(body.username || "");
      const password = String(body.password || "");

      if (!username) return respond({ success: false, error: "missing username" }, 400);
      if (!password) return respond({ success: false, error: "missing password" }, 400);

      const clientIp = getClientIp(req);
      const userAgent = getUserAgent(req);

      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      const recentAttempts = await sb
        .from("login_attempts")
        .select("id", { count: "exact" })
        .eq("username", username)
        .eq("success", false)
        .gte("attempted_at", fiveMinAgo);

      const failCount = recentAttempts.count || 0;

      if (failCount >= 5) {
        await sb.from("login_attempts").insert({
          username, ip_address: clientIp, success: false, user_agent: userAgent
        });
        return respond({ success: false, error: "تم تجاوز عدد المحاولات. انتظر 5 دقائق." }, 429);
      }
      if (failCount >= 3 && failCount < 5) {
        await sb.from("login_attempts").insert({
          username, ip_address: clientIp, success: false, user_agent: userAgent
        });
        return respond({ success: false, error: "محاولات كثيرة. انتظر دقيقتين." }, 429);
      }

      const r = await sb.from("app_users").select("*")
        .eq("username", username).eq("active", true).maybeSingle();

      if (r.error) return respond({ success: false, error: r.error.message }, 500);

      if (!r.data) {
        await sb.from("login_attempts").insert({
          username, ip_address: clientIp, success: false, user_agent: userAgent
        });
        await logAction(sb, req, { username, action: "login_failed", details: { reason: "user_not_found" } });
        return respond({ success: false, error: "invalid" }, 401);
      }

      const user = r.data;
      let valid = false;

      if (user.password_hash && user.salt) {
        const computed = await hashPassword(password, user.salt);
        valid = (computed === user.password_hash);
      } else if (user.password) {
        valid = (user.password === password);
        if (valid) {
          const newSalt = makeSalt();
          const newHash = await hashPassword(password, newSalt);
          await sb.from("app_users").update({
            password_hash: newHash, salt: newSalt, password: null
          }).eq("id", user.id);
        }
      }

      await sb.from("login_attempts").insert({
        username, ip_address: clientIp, success: valid, user_agent: userAgent
      });

      await logAction(sb, req, {
        username,
        action: valid ? "login_success" : "login_failed",
        targetType: "user",
        targetId: user.id,
        targetName: user.name,
        details: { userAgent }
      });

      if (!valid) return respond({ success: false, error: "invalid" }, 401);

      const secret = Deno.env.get("JWT_SECRET") || "";
      if (!secret) return respond({ success: false, error: "server misconfigured" }, 500);

      const now = Math.floor(Date.now() / 1000);
      const token = await signJWT({
        sub: user.id,
        username: user.username,
        role: user.role,
        iat: now,
        exp: now + 24 * 60 * 60
      }, secret);

      return respond({
        success: true,
        token,
        user: {
          id: user.id,
          username: user.username,
          name: user.name,
          role: user.role,
          active: user.active,
          permissions: user.permissions
        }
      });
    }

    // LIST USERS: GET /users (OWNER only)
    if (req.method === "GET") {
      const auth = await requireOwner(req);
      if (!auth.ok) return auth.response;

      const r = await sb.from("app_users")
        .select("id, username, name, role, active, permissions, created_at, updated_at");

      if (r.error) return respond({ success: false, error: r.error.message }, 500);
      return respond({ success: true, users: r.data });
    }

    // CHANGE PASSWORD: POST /users/change-password
    if (req.method === "POST" && url.pathname.endsWith("/change-password")) {
      const auth = await requireAuth(req);
      if (!auth.ok) return auth.response;

      const body = await req.json();
      const userId = String(body.userId || "");
      const newPassword = String(body.newPassword || "");
      const oldPassword = String(body.oldPassword || "");

      if (!userId) return respond({ success: false, error: "missing userId" }, 400);
      if (newPassword.length < 8) {
        return respond({ success: false, error: "كلمة المرور يجب أن تكون 8 أحرف على الأقل" }, 400);
      }

      const isOwner = auth.payload.role === "OWNER";
      const isSelf = auth.payload.sub === userId;

      if (!isOwner && !isSelf) {
        return respond({ success: false, error: "forbidden" }, 403);
      }

      if (!isOwner && isSelf) {
        if (!oldPassword) {
          return respond({ success: false, error: "oldPassword مطلوب" }, 400);
        }
        const userRow = await sb.from("app_users")
          .select("password_hash, salt")
          .eq("id", userId).maybeSingle();
        if (userRow.error || !userRow.data) {
          return respond({ success: false, error: "user not found" }, 404);
        }
        const computedOld = await hashPassword(oldPassword, userRow.data.salt);
        if (computedOld !== userRow.data.password_hash) {
          return respond({ success: false, error: "كلمة المرور القديمة خاطئة" }, 401);
        }
      }

      const salt = makeSalt();
      const hash = await hashPassword(newPassword, salt);
      const r = await sb.from("app_users")
        .update({ password_hash: hash, salt, password: null })
        .eq("id", userId).select().single();

      if (r.error) return respond({ success: false, error: r.error.message }, 500);

      await logAction(sb, req, {
        username: auth.payload.username,
        action: "change_password",
        targetType: "user",
        targetId: r.data.id,
        targetName: r.data.name
      });

      return respond({ success: true, user: r.data });
    }

    // CREATE USER: POST /users (OWNER only)
    if (req.method === "POST") {
      const auth = await requireOwner(req);
      if (!auth.ok) return auth.response;

      const body = await req.json();
      const username = String(body.username || "");
      const password = String(body.password || "");
      const name = String(body.name || "");

      if (!username) return respond({ success: false, error: "missing username" }, 400);
      if (password.length < 8) {
        return respond({ success: false, error: "كلمة المرور يجب أن تكون 8 أحرف على الأقل" }, 400);
      }
      if (!name) return respond({ success: false, error: "missing name" }, 400);

      const check = await sb.from("app_users").select("id").eq("username", username).maybeSingle();
      if (check.data) return respond({ success: false, error: "duplicate" }, 409);

      const salt = makeSalt();
      const hash = await hashPassword(password, salt);
      const role = body.role ? String(body.role) : "EMPLOYEE";
      const permissions = body.permissions || {};

      const r = await sb.from("app_users").insert({
        id: "user-" + Date.now(),
        username,
        password: null,
        password_hash: hash,
        salt,
        name,
        role,
        active: true,
        permissions
      }).select().single();

      if (r.error) return respond({ success: false, error: r.error.message }, 500);

      await logAction(sb, req, {
        username: auth.payload.username,
        action: "create_user",
        targetType: "user",
        targetId: r.data.id,
        targetName: name,
        details: { role }
      });

      return respond({ success: true, user: r.data });
    }

    // UPDATE USER: PUT /users/:id
    if (req.method === "PUT" && last) {
      const auth = await requireAuth(req);
      if (!auth.ok) return auth.response;

      const isOwner = auth.payload.role === "OWNER";
      const isSelf = auth.payload.sub === last;

      if (!isOwner && !isSelf) {
        return respond({ success: false, error: "forbidden" }, 403);
      }

      const body = await req.json();
      delete body.password;
      delete body.password_hash;
      delete body.salt;

      if (!isOwner) {
        delete body.role;
        delete body.permissions;
        delete body.active;
      }

      const r = await sb.from("app_users").update(body).eq("id", last).select().single();
      if (r.error) return respond({ success: false, error: r.error.message }, 500);

      let action = "update_user";
      if (body.active === false) action = "disable_user";
      if (body.active === true) action = "enable_user";

      await logAction(sb, req, {
        username: auth.payload.username,
        action,
        targetType: "user",
        targetId: r.data.id,
        targetName: r.data.name,
        details: body
      });

      return respond({ success: true, user: r.data });
    }

    // DELETE USER: DELETE /users/:id (OWNER only)
    if (req.method === "DELETE" && last) {
      const auth = await requireOwner(req);
      if (!auth.ok) return auth.response;

      if (auth.payload.sub === last) {
        return respond({ success: false, error: "لا يمكنك حذف حسابك" }, 400);
      }

      const beforeDelete = await sb.from("app_users").select("name").eq("id", last).maybeSingle();
      const r = await sb.from("app_users").delete().eq("id", last);
      if (r.error) return respond({ success: false, error: r.error.message }, 500);

      await logAction(sb, req, {
        username: auth.payload.username,
        action: "delete_user",
        targetType: "user",
        targetId: last,
        targetName: beforeDelete.data ? beforeDelete.data.name : "unknown"
      });

      return respond({ success: true });
    }

    return respond({ success: false, error: "not supported" }, 404);

  } catch (error) {
    const msg = error && (error as Error).message ? (error as Error).message : "server error";
    return respond({ success: false, error: msg }, 500);
  }
});
