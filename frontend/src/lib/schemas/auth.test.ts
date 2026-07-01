import { describe, it, expect } from "vitest";
import { loginSchema, signupSchema } from "./auth";

describe("Auth Validation Schemas", () => {
  describe("loginSchema", () => {
    it("should validate correct inputs", () => {
      const result = loginSchema.safeParse({
        username: "testuser",
        password: "securepassword123",
      });
      expect(result.success).toBe(true);
    });

    it("should reject empty username", () => {
      const result = loginSchema.safeParse({
        username: "",
        password: "securepassword123",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe("Username is required");
      }
    });

    it("should reject short password", () => {
      const result = loginSchema.safeParse({
        username: "testuser",
        password: "123",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe("Password must be at least 6 characters");
      }
    });
  });

  describe("signupSchema", () => {
    it("should validate correct inputs", () => {
      const result = signupSchema.safeParse({
        username: "test_user_1",
        email: "test@example.com",
        password: "securepassword123",
      });
      expect(result.success).toBe(true);
    });

    it("should reject invalid email formats", () => {
      const result = signupSchema.safeParse({
        username: "testuser",
        email: "invalid-email",
        password: "securepassword123",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe("Invalid email format");
      }
    });

    it("should accept emails or special characters in username", () => {
      const result = signupSchema.safeParse({
        username: "test@example.com",
        email: "test@example.com",
        password: "securepassword123",
      });
      expect(result.success).toBe(true);
    });
  });
});
