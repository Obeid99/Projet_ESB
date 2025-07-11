'use client';

import {
  Box,
  Button,
  Input,
  VStack,
  Text,
  Flex,
  InputGroup,
  InputRightElement,
  IconButton,
  useToast
} from '@chakra-ui/react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { IoEye, IoEyeOff } from 'react-icons/io5';

export default function AdminLoginPage() {
  const router = useRouter();
  const toast = useToast();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');

  const showToast = (title: string, description: string, status: 'success' | 'error') => {
    toast({
      title,
      description,
      status,
      duration: 3000,
      isClosable: true,
      position: 'top',
      variant: 'solid',
      containerStyle: { color: 'white' }
    });
  };

  const handleLogin = async () => {
    setLoginError('');

    if (!username || !password) {
      setLoginError('Please enter valid credentials.');
      showToast('Missing credentials', 'Please enter both username and password.', 'error');
      return;
    }

    try {
      const res = await fetch('http://127.0.0.1:5000/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (data.success) {
        showToast('Admin login successful!', 'You are now logged in as admin.', 'success');
        setTimeout(() => router.push('/administration-dashboard'), 800);
      } else {
        const errorMsg = data.error || 'Login failed';
        setLoginError(errorMsg);
        showToast('Login failed', errorMsg, 'error');
      }
    } catch {
      setLoginError('Server error. Please try again later.');
      showToast('Server error', 'Could not connect to backend.', 'error');
    }
  };

  return (
    <Flex w="100vw" h="100vh" alignItems="center" justifyContent="center" bg="gray.100">
      <Box
        w={{ base: '95vw', md: '800px' }}
        h={{ base: 'auto', md: '500px' }}
        display="flex"
        boxShadow="2xl"
        borderRadius="lg"
        overflow="hidden"
      >
        {/* Left: Login Card */}
        <Box flex={1} bg="white" p={{ base: 6, md: 10 }} display="flex" flexDirection="column" justifyContent="center">
          <Box w="100%" maxW="350px" mx="auto">
            <VStack spacing="20px" w="100%">
              <img src="/img/esb.png" alt="Logo" style={{ width: 60, marginBottom: 10 }} />
              <Text fontSize="2xl" fontWeight="bold" color="red.500">
                Admin Login
              </Text>

              {loginError && (
                <Box color="red.500" fontWeight="bold" w="100%" textAlign="center">
                  {loginError}
                </Box>
              )}

              <Input
                placeholder="Admin Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />

              <InputGroup>
                <Input
                  placeholder="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleLogin();
                  }}
                />
                <InputRightElement>
                  <IconButton
                    aria-label="Toggle Password Visibility"
                    icon={showPassword ? <IoEye /> : <IoEyeOff />}
                    size="sm"
                    onClick={() => setShowPassword(!showPassword)}
                  />
                </InputRightElement>
              </InputGroup>

              <Button colorScheme="red" w="100%" onClick={handleLogin}>
                Login
              </Button>
            </VStack>
          </Box>
        </Box>

        {/* Right: Info Card */}
        <Box
          flex={1}
          bgGradient="linear(to-br, red.500, red.400)"
          color="white"
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          p={{ base: 6, md: 10 }}
        >
          <Text fontSize="2xl" fontWeight="bold" mb="4">
            Admin Portal
          </Text>
          <Text fontSize="md" mb="6" textAlign="center" maxW="300px">
            Access the admin dashboard to manage the ESB Multi-Agent Chatbot. Only authorized administrators can log in here.
          </Text>
        </Box>
      </Box>
    </Flex>
  );
}
