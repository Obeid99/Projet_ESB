'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Button,
  Input,
  VStack,
  Text,
  Flex,
  Checkbox,
  Image,
  InputGroup,
  InputRightElement,
  IconButton,
  useToast,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { IoEye, IoEyeOff } from 'react-icons/io5';
import logo from '/public/img/esb.png';
import { BsRobot } from 'react-icons/bs';

export default function LoginClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get('redirect') || '/welcome';
  const [isFlipped, setIsFlipped] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [registerUsername, setRegisterUsername] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loginSuccess, setLoginSuccess] = useState(false);
  const [loginError, setLoginError] = useState('');
  const toast = useToast();

  const handleLogin = async () => {
    setLoginError('');
    if (!username || !password) {
      setLoginError('Please enter valid credentials.');
      toast({
        title: 'Missing credentials',
        description: 'Please enter both username and password.',
        status: 'error',
        duration: 3000,
        isClosable: true,
        position: 'top',
        variant: 'solid',
        containerStyle: { color: 'white' },
      });
      return;
    }
    try {
      const res = await fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.success) {
        setLoginSuccess(true);
        setLoginError('');
        toast({
          title: 'Login successful!',
          description: 'You are now logged in.',
          status: 'success',
          duration: 2000,
          isClosable: true,
          position: 'top',
          variant: 'solid',
          containerStyle: { color: 'white' },
        });
        setTimeout(() => {
          router.push(redirectPath);
        }, 800);
      } else {
        setLoginError(data.error || 'Login failed');
        toast({
          title: 'Login failed',
          description: data.error || 'Invalid credentials.',
          status: 'error',
          duration: 3000,
          isClosable: true,
          position: 'top',
          variant: 'solid',
          containerStyle: { color: 'white' },
        });
      }
    } catch (err) {
      setLoginError('Server error. Please try again later.');
      toast({
        title: 'Server error',
        description: 'Could not connect to backend.',
        status: 'error',
        duration: 3000,
        isClosable: true,
        position: 'top',
        variant: 'solid',
        containerStyle: { color: 'white' },
      });
    }
  };

  useEffect(() => {
    if (loginSuccess) {
      localStorage.setItem('authenticated', 'true');
    }
  }, [loginSuccess]);

  const handleRegister = async () => {
    if (!registerUsername || !registerPassword || !confirmPassword) {
      toast({
        title: 'Missing fields',
        description: 'Please fill in all fields.',
        status: 'error',
        duration: 3000,
        isClosable: true,
        position: 'top',
        variant: 'solid',
        containerStyle: { color: 'white' },
      });
      return;
    }
    if (registerPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please make sure your passwords match.',
        status: 'error',
        duration: 3000,
        isClosable: true,
        position: 'top',
        variant: 'solid',
        containerStyle: { color: 'white' },
      });
      return;
    }
    try {
      const res = await fetch('http://127.0.0.1:5000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username: registerUsername, password: registerPassword }),
      });
      const data = await res.json();
      if (data.success) {
        toast({
          title: 'Registration successful!',
          description: 'You can now log in.',
          status: 'success',
          duration: 2000,
          isClosable: true,
          position: 'top',
          variant: 'solid',
          containerStyle: { color: 'white' },
        });
        setIsFlipped(false);
        setRegisterUsername('');
        setRegisterPassword('');
        setConfirmPassword('');
      } else {
        toast({
          title: 'Registration failed',
          description: data.error || 'Registration failed.',
          status: 'error',
          duration: 3000,
          isClosable: true,
          position: 'top',
          variant: 'solid',
          containerStyle: { color: 'white' },
        });
      }
    } catch (err) {
      toast({
        title: 'Server error',
        description: 'Could not connect to backend.',
        status: 'error',
        duration: 3000,
        isClosable: true,
        position: 'top',
        variant: 'solid',
        containerStyle: { color: 'white' },
      });
    }
  };

  return (
    <Flex w="100vw" h="100vh" alignItems="center" justifyContent="center" bg="gray.100">
      <Box w={{ base: '95vw', md: '800px' }} h={{ base: 'auto', md: '500px' }} display="flex" boxShadow="2xl" borderRadius="lg" overflow="hidden">
        {/* Left (Login/Register) */}
        <Box flex={1} bg="white" p={{ base: 6, md: 10 }} display="flex" flexDirection="column" justifyContent="center">
          <Box w="100%" maxW="350px" mx="auto">
            <Box w="100%" h="100%" position="relative" style={{ perspective: '1000px' }}>
              <Box
                w="100%"
                h="100%"
                position="relative"
                transition="transform 0.6s"
                transform={isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'}
                style={{ transformStyle: 'preserve-3d' }}
              >
                {/* Login Form */}
                <Box position="absolute" w="100%" h="100%" style={{ backfaceVisibility: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <VStack spacing="10px" w="100%" maxW="350px" mx="auto">
                    <Image src={logo.src} alt="Logo" boxSize="60px" mx="auto" mb="10px" />
                    <Text fontSize="2xl" fontWeight="bold" mb="10px" color="red.500">Login</Text>
                    <form style={{ width: '100%' }} onSubmit={e => { e.preventDefault(); handleLogin(); }}>
                      {loginError && (
                        <Alert status="error" borderRadius="md" mb={2} colorScheme="red" w="100%">
                          <AlertIcon />
                          {loginError}
                        </Alert>
                      )}
                      <Input
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        autoComplete="username"
                        onKeyDown={e => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleLogin();
                          }
                        }}
                        mb={2}
                      />
                      <InputGroup mb={2}>
                        <Input
                          placeholder="Password"
                          type={showPassword ? 'text' : 'password'}
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleLogin();
                            }
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
                      <Checkbox alignSelf="start" mb={2}>Remember Me</Checkbox>
                      <Button colorScheme="red" w="100%" type="submit" mb={2}>Login</Button>
                    </form>
                    <Button
                      variant="ghost"
                      color="blue.600"
                      fontWeight="bold"
                      fontSize="md"
                      w="100%"
                      mt={2}
                      bg="blue.50"
                      _hover={{ bg: 'blue.100', textDecoration: 'underline' }}
                      _active={{ bg: 'blue.200' }}
                      borderRadius="md"
                      onClick={() => setIsFlipped(true)}
                      zIndex={1}
                    >
                      You don't have an account? Sign up
                    </Button>
                  </VStack>
                </Box>
                {/* Register Form */}
                <Box position="absolute" w="100%" h="100%" style={{ backfaceVisibility: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }} transform="rotateY(180deg)">
                  <VStack spacing="10px" w="100%" maxW="350px" mx="auto">
                    <Image src={logo.src} alt="Logo" boxSize="60px" mx="auto" mb="10px" />
                    <Text fontSize="2xl" fontWeight="bold" mb="10px" color="red.500">Register</Text>
                    <Input
                      placeholder="Username"
                      value={registerUsername}
                      onChange={(e) => setRegisterUsername(e.target.value)}
                      autoComplete="username"
                    />
                    <InputGroup>
                      <Input
                        placeholder="Password"
                        type={showRegisterPassword ? 'text' : 'password'}
                        value={registerPassword}
                        onChange={(e) => setRegisterPassword(e.target.value)}
                      />
                      <InputRightElement>
                        <IconButton
                          aria-label="Toggle Password Visibility"
                          icon={showRegisterPassword ? <IoEye /> : <IoEyeOff />}
                          size="sm"
                          onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                        />
                      </InputRightElement>
                    </InputGroup>
                    <InputGroup>
                      <Input
                        placeholder="Confirm Password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                      />
                      <InputRightElement>
                        <IconButton
                          aria-label="Toggle Confirm Password Visibility"
                          icon={showConfirmPassword ? <IoEye /> : <IoEyeOff />}
                          size="sm"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        />
                      </InputRightElement>
                    </InputGroup>
                    <Button colorScheme="red" w="100%" onClick={handleRegister}>Register</Button>
                    <Button
                      variant="ghost"
                      color="blue.600"
                      fontWeight="bold"
                      fontSize="md"
                      w="100%"
                      mt={2}
                      bg="blue.50"
                      _hover={{ bg: 'blue.100', textDecoration: 'underline' }}
                      _active={{ bg: 'blue.200' }}
                      borderRadius="md"
                      onClick={() => {
                        setIsFlipped(false);
                      }}
                    >
                      Already have an account? Login
                    </Button>
                  </VStack>
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
        {/* Right (Red Info) */}
        <Box flex={1} bgGradient="linear(to-br, red.500, red.400)" color="white" display="flex" flexDirection="column" alignItems="center" justifyContent="center" p={{ base: 6, md: 10 }}>
          <Box mb={6} display="flex" flexDirection="column" alignItems="center">
            <BsRobot size={110} color="white" style={{ filter: 'drop-shadow(0 4px 24px rgba(0,0,0,0.30))' }} />
          </Box>
          <Text fontSize="2xl" fontWeight="bold" mb="4">Welcome to ESB Chatbot</Text>
          <Text fontSize="md" mb="6" textAlign="center" maxW="300px">
            Access your account or create a new one to interact with the ESB Multi-Agent Chatbot. If you don't have an account, click Sign up!
          </Text>
          <Button
            variant="outline"
            colorScheme="whiteAlpha"
            borderColor="white"
            color="white"
            _hover={{ bg: 'whiteAlpha.200' }}
            onClick={() => {
              setIsFlipped(true);
              setTimeout(() => {
                const regBox = document.querySelector('[transform="rotateY(180deg)"]');
                if (regBox) regBox.scrollIntoView({ block: 'center', behavior: 'smooth' });
              }, 400);
            }}
          >
            SIGN UP
          </Button>
        </Box>
      </Box>
    </Flex>
  );
}
