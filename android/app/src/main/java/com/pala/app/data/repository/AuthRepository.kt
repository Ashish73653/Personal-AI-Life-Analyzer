package com.pala.app.data.repository

import com.pala.app.data.local.TokenStorage
import com.pala.app.data.remote.dto.LoginRequest
import com.pala.app.data.remote.dto.RefreshRequest
import com.pala.app.data.remote.dto.RegisterRequest
import com.pala.app.data.remote.service.AuthApi
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val authApi: AuthApi,
    private val tokenStorage: TokenStorage,
) {

    suspend fun register(email: String, password: String): Result<Unit> = runCatching {
        val response = authApi.register(RegisterRequest(email = email, password = password))
        if (!response.success || response.data == null) {
            throw IllegalStateException(response.error ?: "Registration failed")
        }
        tokenStorage.save(
            accessToken = response.data.tokens.access_token,
            refreshToken = response.data.tokens.refresh_token,
        )
    }

    suspend fun login(email: String, password: String): Result<Unit> = runCatching {
        val response = authApi.login(LoginRequest(email = email, password = password))
        if (!response.success || response.data == null) {
            throw IllegalStateException(response.error ?: "Login failed")
        }
        tokenStorage.save(
            accessToken = response.data.tokens.access_token,
            refreshToken = response.data.tokens.refresh_token,
        )
    }

    suspend fun refreshTokens(): Result<Unit> = runCatching {
        val refreshToken = tokenStorage.refreshToken() ?: throw IllegalStateException("No refresh token")
        val response = authApi.refresh(RefreshRequest(refresh_token = refreshToken))
        if (!response.success || response.data == null) {
            throw IllegalStateException(response.error ?: "Token refresh failed")
        }
        tokenStorage.save(
            accessToken = response.data.tokens.access_token,
            refreshToken = response.data.tokens.refresh_token,
        )
    }

    fun logout() {
        tokenStorage.clear()
    }
}
