import { fetchEngine } from '../utils/processUtils'

export interface User {
    id: string
    firstName?: string
    lastName?: string
    email?: string
}

interface UserCredentials {
    password: string
}

export interface UserProfile {
    profile: User
    credentials?: UserCredentials
}

class CamundaUserClient {
    // Fetch a single user by ID
    async getUser(userId: string): Promise<User> {
        const response = await fetchEngine(`user/${userId}/profile`)
        if (!response.ok) throw new Error('Failed to fetch user', { cause: response })
        return response.json() as Promise<User>
    }

    // Create a new user
    async createUser(userData: UserProfile): Promise<void> {
        const response = await fetchEngine(`user/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: 'Basic ' + btoa('demo:demo'),
            },
            body: JSON.stringify(userData),
        })
        if (!response.ok) throw new Error('Failed to create user')
    }

    // Update a user
    async updateUser(userId: string, userData: UserProfile): Promise<void> {
        const response = await fetchEngine(`user/${userId}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: 'Basic ' + btoa('demo:demo'),
            },
            body: JSON.stringify(userData),
        })
        if (!response.ok) throw new Error('Failed to update user')
    }

    // Delete a user
    async deleteUser(userId: string): Promise<void> {
        const response = await fetchEngine(`user/${userId}`, {
            method: 'DELETE',
            headers: {
                Authorization: 'Basic ' + btoa('demo:demo'),
            },
        })
        if (!response.ok) throw new Error('Failed to delete user')
    }

    // Update a user
    async createGroupMember(groupId: string, userId: string): Promise<void> {
        const response = await fetchEngine(`group/${groupId}/members/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: 'Basic ' + btoa('demo:demo'),
            },
        })
        if (!response.ok) throw new Error('Failed to create group member')
    }
}

const client = new CamundaUserClient()

export default client