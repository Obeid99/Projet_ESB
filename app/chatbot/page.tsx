'use client';

import {
  Box,
  Input,
  Button,
  VStack,
  Text,
  Flex,
  Icon,
  Image,
  InputGroup,
  InputLeftElement,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  HStack,
  useToast
} from '@chakra-ui/react';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  IoArrowBack,
  IoLogOut,
  IoSend,
  IoSearch,
  IoPersonCircle,
  IoCopy,
  IoRefresh
} from 'react-icons/io5';
import axios from 'axios';

export default function ChatbotPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<{ text: string; sender: 'bot' | 'user' }[]>([]);
  const [input, setInput] = useState('');
  const [agentActive, setAgentActive] = useState(false);
  const toast = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([{ text: "Bonjour, comment peux-je vous aider aujourd'hui?", sender: 'bot' }]);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (overrideInput?: string) => {
    const messageToSend = overrideInput ?? input;
    if (messageToSend.trim()) {
      setMessages(prev => [...prev, { text: messageToSend, sender: 'user' }]);
      setAgentActive(true);
      setInput('');

      toast({
        title: 'Generating response...',
        status: 'info',
        duration: 2000,
        isClosable: true
      });

      try {
        const res = await axios.post(
          'http://127.0.0.1:5000/api/chat',
          { message: messageToSend },
          { withCredentials: true }
        );
        setMessages(prev => [...prev, { text: res.data.response, sender: 'bot' }]);
      } catch {
        setMessages(prev => [
          ...prev,
          { text: 'Error: Unable to connect to backend.', sender: 'bot' }
        ]);
      }
      setAgentActive(false);
      toast.closeAll();
    }
  };

  const handleExampleClick = (example: string) => {
    setInput(example);
    setTimeout(() => handleSend(example), 0);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied!',
      description: 'Message copied to clipboard.',
      status: 'success',
      duration: 2000,
      isClosable: true
    });
  };

  const handleRefresh = () => {
    toast({
      title: 'Refreshed!',
      description: 'This would trigger a message refresh.',
      status: 'info',
      duration: 2000,
      isClosable: true
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('authenticated');
    router.push('/login');
  };

  return (
    <Flex w="100vw" h="100vh" overflow="hidden">
      {/* Sidebar */}
      <Flex direction="column" w="250px" bg="red.500" color="white" p="20px" justifyContent="space-between">
        <Box>
          <Box mb="9" display="flex" flexDirection="column" alignItems="center">
            <Image src="/img/esb.png" boxSize="100px" borderRadius="full" border="3px solid white" mb="4" />
          </Box>
          <Button
            leftIcon={<IoArrowBack />}
            w="full"
            bg="white"
            color="red.500"
            _hover={{ bg: 'red.100' }}
            _active={{ bg: 'red.200' }}
            onClick={() => router.push('/welcome')}
            mb="6"
          >
            Back
          </Button>
        </Box>
        <Button
          leftIcon={<IoLogOut />}
          w="full"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          onClick={handleLogout}
        >
          Log Out
        </Button>
      </Flex>

      {/* Chat Area */}
      <Flex flex="1" direction="column" p="20px" bg="gray.100" minH="0">
        {/* Top Bar */}
        <Flex justifyContent="space-between" mb="10px">
          <InputGroup w="300px">
            <InputLeftElement pointerEvents="none">
              <Icon as={IoSearch} color="gray.400" />
            </InputLeftElement>
            <Input placeholder="Search..." bg="white" borderRadius="md" />
          </InputGroup>
          <Menu>
            <MenuButton>
              <Icon as={IoPersonCircle} w="40px" h="40px" color="gray.600" cursor="pointer" />
            </MenuButton>
            <MenuList>
              <MenuItem>
                <Text fontWeight="bold">Zayneb Zouaoui</Text>
              </MenuItem>
            </MenuList>
          </Menu>
        </Flex>

        <Flex flex="1" minH="0" overflow="hidden">
          {/* Main Chatbox */}
          <Flex flex="1" direction="column" align="center" justify="center" minH="0" h="100%" overflow="hidden">
            <Box w="100%" maxW="900px" h="80%" bg="white" borderRadius="lg" boxShadow="md" p="20px" display="flex" flexDirection="column">
              <Text fontSize="2xl" fontWeight="bold" mb="4" color="red.500" textAlign="center" w="100%">
                Student Chatbot
              </Text>

              <Box
                ref={scrollRef}
                flex="1"
                overflowY="auto"
                p="10px"
                bg="gray.50"
                borderRadius="md"
                boxShadow="inner"
                mb="4"
              >
                {messages.map((msg, idx) => (
                  <Flex
                    key={idx}
                    justify={msg.sender === 'bot' ? 'flex-start' : 'flex-end'}
                    align="flex-end"
                    mb="2"
                  >
                    {msg.sender === 'bot' && (
                      <Image
                        src="/img/esb.png"
                        boxSize="32px"
                        borderRadius="full"
                        mr="8px"
                        border="2px solid #f87171"
                        alt="Bot"
                      />
                    )}
                    <Box
                      bg={msg.sender === 'bot' ? 'red.100' : 'blue.100'}
                      p="10px"
                      borderRadius="md"
                      maxW="70%"
                    >
                      <Text>{msg.text}</Text>
                    </Box>
                    {msg.sender === 'bot' && (
                      <HStack spacing="2" ml="2">
                        <Icon as={IoCopy} boxSize="4" color="gray.500" cursor="pointer" onClick={() => handleCopy(msg.text)} />
                        <Icon as={IoRefresh} boxSize="4" color="gray.500" cursor="pointer" onClick={handleRefresh} />
                      </HStack>
                    )}
                    {msg.sender === 'user' && (
                      <Image
                        src="/img/user.jpg"
                        boxSize="32px"
                        borderRadius="full"
                        ml="8px"
                        border="2px solid #3b82f6"
                        alt="User"
                      />
                    )}
                  </Flex>
                ))}
              </Box>

              <Flex>
                <Input
                  placeholder="Type your message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  flex="1"
                  borderRadius="md"
                  bg="gray.50"
                />
                <Button
                  ml="2"
                  colorScheme="red"
                  onClick={() => handleSend()}
                  isLoading={agentActive}
                  loadingText="Sending"
                  borderRadius="full"
                  w="44px"
                  h="44px"
                  p="0"
                >
                  <Icon as={IoSend} boxSize="5" />
                </Button>
              </Flex>
            </Box>
          </Flex>

          {/* Right Sidebar */}
          <Box w="300px" bg="white" borderRadius="lg" boxShadow="md" p="20px" ml="20px">
            <Text fontSize="lg" fontWeight="bold" mb="4" color="gray.700">
              Agent Status
            </Text>
            <VStack align="start" spacing="2" mb="6">
              <Text>SentimentAgent</Text>
              <Text>IntentAgent</Text>
              <Text>WebAgent</Text>
            </VStack>
            <Text fontSize="lg" fontWeight="bold" mb="4" color="gray.700">
              Try These Examples
            </Text>
            <VStack align="start" spacing="2">
              {[
                "I love the entrepreneurship program at ESB!",
                "I'm frustrated with the registration system!",
                "What are the library hours?",
                "I need career guidance for my future",
                "Thank you for the excellent support!",
                "J'adore ESB!"
              ].map((example, i) => (
                <Text
                  key={i}
                  as="span"
                  cursor="pointer"
                  _hover={{ textDecoration: 'underline', color: 'red.500' }}
                  onClick={() => handleExampleClick(example)}
                >
                  {example}
                </Text>
              ))}
            </VStack>
          </Box>
        </Flex>
      </Flex>
    </Flex>
  );
}
