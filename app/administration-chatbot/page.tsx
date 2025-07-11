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
import {
  IoArrowBack,
  IoLogOut,
  IoSend,
  IoSearch,
  IoPersonCircle,
  IoCopy,
  IoRefresh,
  IoBarChart,
  IoChatbubbles
} from 'react-icons/io5';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function AdministrationChatbotPage() {
  const router = useRouter();
  const toast = useToast();
  const [messages, setMessages] = useState<{ text: string; sender: 'bot' | 'user' }[]>([]);
  const [input, setInput] = useState('');
  const [agentActive, setAgentActive] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([{ text: "Bonjour, comment puis-je vous aider en tant qu'administrateur ?", sender: 'bot' }]);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleExampleClick = (example: string) => {
    setInput(example);
    setTimeout(() => handleSend(example), 0);
  };

  const handleSend = async (overrideInput?: string) => {
    const messageToSend = overrideInput || input;
    if (!messageToSend.trim()) return;

    setMessages(prev => [...prev, { text: messageToSend, sender: 'user' }]);
    setInput('');
    setAgentActive(true);

    toast({
      title: 'Generating response...',
      status: 'info',
      duration: 2000,
      isClosable: true
    });

    setTimeout(async () => {
      try {
        const res = await axios.post(
          'http://127.0.0.1:5000/admin/api/chat',
          { message: messageToSend },
          { withCredentials: true }
        );
        setMessages(prev => [...prev, { text: res.data.response, sender: 'bot' }]);
      } catch {
        setMessages(prev => [...prev, { text: 'Error: Unable to connect to backend.', sender: 'bot' }]);
      } finally {
        setAgentActive(false);
        toast.closeAll();
      }
    }, 2000);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Message Copied',
      description: 'The message has been copied to your clipboard.',
      status: 'success',
      duration: 2000,
      isClosable: true,
      position: 'top'
    });
  };

  const handleRefresh = () => {
    toast({
      title: 'Refreshing...',
      description: 'The answer will be refreshed soon.',
      status: 'info',
      duration: 1800,
      isClosable: true,
      position: 'top'
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('authenticated');
    router.push('/administration-login');
  };

  return (
    <Flex w="100vw" h="100vh" overflow="hidden">
      {/* Sidebar */}
      <Flex direction="column" w="250px" bg="red.500" color="white" p="20px" justifyContent="space-between">
        <Box>
          <Box mb="9" display="flex" flexDirection="column" alignItems="center" w="100%">
            <Image
              src="/img/esb.png"
              boxSize="120px"
              borderRadius="full"
              mb="4"
              border="3px solid white"
            />
          </Box>
          <Button onClick={() => router.push('/welcome')} leftIcon={<IoArrowBack />} bg="white" color="red.500" w="full" mb="10px">Back</Button>
          <Button onClick={() => router.push('/administration-dashboard')} leftIcon={<IoBarChart />} bg="white" color="red.500" w="full" mb="10px">Dashboard</Button>
          <Button onClick={() => router.push('/administration-chatbot')} leftIcon={<IoChatbubbles />} bg="white" color="red.500" w="full" mb="20px">Chatbot</Button>
        </Box>
        <Button onClick={handleLogout} leftIcon={<IoLogOut />} bg="white" color="red.500" w="full">Log Out</Button>
      </Flex>

      {/* Main Content */}
      <Flex flex="1" direction="column" bg="gray.100" p="20px" minH="0">
        {/* Header */}
        <Flex justifyContent="space-between" alignItems="center" mb="10px">
          <InputGroup w="300px">
            <InputLeftElement pointerEvents="none">
              <Icon as={IoSearch} color="gray.400" />
            </InputLeftElement>
            <Input placeholder="Search..." bg="white" borderRadius="md" />
          </InputGroup>
          <Menu>
            <MenuButton><Icon as={IoPersonCircle} w="40px" h="40px" color="gray.600" cursor="pointer" /></MenuButton>
            <MenuList>
              <MenuItem><Text fontWeight="bold">Admin User</Text></MenuItem>
            </MenuList>
          </Menu>
        </Flex>

        <Flex flex="1" overflow="hidden">
          {/* Chatbot Content */}
          <Flex flex="1" direction="column" alignItems="center" justifyContent="center" minH="0">
            <Box w="80%" h="80%" bg="white" borderRadius="md" boxShadow="md" p="20px" display="flex" flexDirection="column" minH="0">
              <Text fontSize="2xl" fontWeight="bold" mb="20px" color="red.500" textAlign="center" w="100%">Administration Chatbot</Text>
              <VStack spacing="10px" align="start" h="100%" flex="1" minH="0">
                <Box
                  ref={scrollRef}
                  w="100%"
                  flex="1"
                  bg="gray.50"
                  borderRadius="md"
                  overflowY="auto"
                  p="10px"
                  boxShadow="inner"
                  minH="0"
                  maxH="100%"
                >
                  {messages.map((msg, idx) => (
                    <Flex key={idx} justifyContent={msg.sender === 'bot' ? 'flex-start' : 'flex-end'} alignItems="flex-end" mb="5px">
                      {msg.sender === 'bot' && (
                        <Image src="/img/esb.png" boxSize="32px" borderRadius="full" mr="8px" border="2px solid #f87171" alt="Bot" />
                      )}
                      <Box bg={msg.sender === 'bot' ? 'red.100' : 'blue.100'} p="10px" borderRadius="md" maxW="70%">
                        <Text>{msg.text}</Text>
                      </Box>
                      {msg.sender === 'bot' && (
                        <HStack spacing="5px" ml="10px">
                          <Icon as={IoCopy} w="16px" h="16px" color="gray.500" cursor="pointer" onClick={() => handleCopy(msg.text)} />
                          <Icon as={IoRefresh} w="16px" h="16px" color="gray.500" cursor="pointer" onClick={handleRefresh} />
                        </HStack>
                      )}
                      {msg.sender === 'user' && (
                        <Icon as={IoPersonCircle} w="32px" h="32px" color="#3b82f6" ml="8px" />
                      )}
                    </Flex>
                  ))}
                </Box>

                {/* Input Row */}
                <Flex w="100%" alignItems="center">
                  <Input
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSend();
                    }}
                    flex="1"
                    borderRadius="md"
                    bg="gray.50"
                  />
                  <Button
                    ml="10px"
                    colorScheme="red"
                    onClick={() => handleSend()}
                    p="0"
                    w="40px"
                    h="40px"
                    borderRadius="full"
                    isLoading={agentActive}
                  >
                    <Icon as={IoSend} w="20px" h="20px" />
                  </Button>
                </Flex>
              </VStack>
            </Box>
          </Flex>

          {/* Right Sidebar */}
          <Box w="300px" bg="white" borderRadius="md" boxShadow="md" p="20px" ml="20px">
            <Text fontSize="lg" fontWeight="bold" mb="10px" color="gray.700">Agent Status</Text>
            <VStack spacing="5px" align="start" mb="20px">
              <Text> SentimentAgent </Text>
              <Text> IntentAgent </Text>
              <Text> WebAgent </Text>
            </VStack>
            <Text fontSize="lg" fontWeight="bold" mb="10px" color="gray.700">Try These Examples</Text>
            <VStack spacing="5px" align="start">
              {[
                "Show me all pending student requests.",
                "How many students are registered this semester?",
                "Generate a report for course enrollments.",
                "List all upcoming administrative meetings.",
                "Update the academic calendar."
              ].map((ex, idx) => (
                <Text
                  key={idx}
                  as="span"
                  cursor="pointer"
                  _hover={{ textDecoration: 'underline', color: 'red.500' }}
                  onClick={() => handleExampleClick(ex)}
                >{ex}</Text>
              ))}
            </VStack>
          </Box>
        </Flex>
      </Flex>
    </Flex>
  );
}
